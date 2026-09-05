"""The network's internal-traffic contract — the analytics point of truth.

The rule (https://2plot.ai/docs/satellite-analytics, "Internal traffic"): a
request whose User-Agent contains `2plot-internal` is 2plot machinery talking
to itself — the hub's hourly health sweep, CI smoke batteries, the 4x-daily
heartbeat, cross-app calls — and is counted NOWHERE. Dropped at write time,
before device detection and before bot classification. `/healthz` is never a
visit either.

Both halves are tested here, because a contract kept on only one side is not
kept at all:

*inbound*   token-carrying requests never reach the ledger, and therefore
            never reach `human_hits` / `bot_hits` in the hourly rollup this
            app POSTs to 2plot.ai;
*outbound*  every call this host makes to another network host sends
            `INTERNAL_UA`, so the far side can apply the same rule. That half
            was missing: the ad client fetched a campaign from 2plot.dev on
            every single docs page view, arriving as `python-requests/2.x`,
            and the hub counted this satellite's readers as its own bots.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from conftest import BROWSER_UA, CRAWLER_UA
from lib.analytics_tracker import analytics_path, tracker
from lib.constants import INTERNAL_UA, INTERNAL_UA_TOKEN, internal_ua

# A real page. `lib/traffic_rollup` drops infrastructure paths (`/llms.txt`,
# `/robots.txt`, `/healthz`, ...) at read time, so a rollup assertion made
# against one of those would pass no matter what the tracker did.
PAGE = "/getting-started"


def _ledger_visits():
    """Every hit on disk, flushing the write buffer first."""
    tracker.flush()
    try:
        with open(analytics_path()) as f:
            return json.load(f).get("visits", [])
    except FileNotFoundError:
        return []


def _rollup():
    """Today's rollup as the hub would receive it, or an all-zero stand-in."""
    from lib.traffic_rollup import daily_rollup

    tracker.flush()
    return daily_rollup("pannellum", datetime.now().date()) or {
        "human_hits": 0, "bot_hits": 0,
    }


# --------------------------------------------------------------- the token --


def test_token_is_the_network_wide_string():
    """The contract only works if every host agrees on the byte sequence."""
    assert INTERNAL_UA_TOKEN == "2plot-internal"
    assert INTERNAL_UA_TOKEN in INTERNAL_UA
    assert INTERNAL_UA.startswith(INTERNAL_UA_TOKEN)


def test_caller_suffix_never_breaks_the_token():
    ua = internal_ua("traffic-reporter")
    assert INTERNAL_UA_TOKEN in ua
    assert ua.endswith("traffic-reporter")
    assert internal_ua() == INTERNAL_UA
    assert internal_ua("  ") == INTERNAL_UA


# ------------------------------------------------------------------ inbound --


def test_the_tests_can_see_the_ledger_at_all(client, tmp_state_dir):
    """Guard for every delta assertion below.

    If the ledger path were wrong (or the suite were writing into the repo's
    own visitor_analytics.json), every "count did not change" test would pass
    vacuously. Prove a write lands first.
    """
    assert str(analytics_path()).startswith(tmp_state_dir), analytics_path()
    before = len(_ledger_visits())
    client.get(PAGE, user_agent=BROWSER_UA)
    assert len(_ledger_visits()) == before + 1


def test_internal_ua_is_counted_nowhere(client):
    before = len(_ledger_visits())
    client.get(PAGE, user_agent=internal_ua("network-smoke"))
    client.get("/", user_agent=INTERNAL_UA)
    assert len(_ledger_visits()) == before


def test_a_crawler_shaped_probe_carrying_the_token_stays_internal(client):
    """The battery's crawler probe exercises the bot path deliberately.

    It must still not be counted. This is precisely why the drop happens
    before `detect_device_type` — classification would file it under `bot`.
    """
    before = len(_ledger_visits())
    client.get(PAGE, user_agent=f"{CRAWLER_UA} {INTERNAL_UA}")
    assert len(_ledger_visits()) == before


def test_the_token_is_matched_case_insensitively(client):
    before = len(_ledger_visits())
    client.get(PAGE, user_agent="2PLOT-INTERNAL/1.0 Health-Sweep")
    assert len(_ledger_visits()) == before


def test_healthz_is_never_a_visit(client):
    before = len(_ledger_visits())
    client.get("/healthz", user_agent="Render/1.0 health-check")
    client.get("/healthz", user_agent=BROWSER_UA)
    assert len(_ledger_visits()) == before


# ----------------------------------------------- the reported numbers -------
#
# The exclusion that actually matters. Everything above is about the ledger;
# this is about what 2plot.ai charts.


def test_internal_traffic_is_absent_from_human_hits_and_bot_hits(client):
    before = _rollup()

    # Four calls that are all machinery, in the two shapes the network sends:
    # a plain internal UA, and a crawler-shaped probe carrying the token.
    for _ in range(2):
        client.get(PAGE, user_agent=internal_ua("network-smoke"))
        client.get(PAGE, user_agent=f"{CRAWLER_UA} {INTERNAL_UA}")

    after = _rollup()
    assert after["human_hits"] == before["human_hits"], (
        "internal traffic reached human_hits — the hub would chart the health "
        "sweep as readers of these docs"
    )
    assert after["bot_hits"] == before["bot_hits"], (
        "internal traffic reached bot_hits — the hub would chart CI as crawler "
        "interest"
    )


def test_real_traffic_is_still_counted(client):
    """The exclusions must not have lobotomised the tracker.

    A rule that drops everything also satisfies every assertion above, so the
    positive case is load-bearing: one browser hit is one human, one Googlebot
    hit is one bot.
    """
    before = _rollup()
    client.get(PAGE, user_agent=BROWSER_UA)
    client.get(PAGE, user_agent=CRAWLER_UA)
    after = _rollup()

    assert after["human_hits"] == before["human_hits"] + 1
    assert after["bot_hits"] == before["bot_hits"] + 1


# ----------------------------------------------------------------- outbound --


class _Captured(Exception):
    """Abort the request once the headers have been seen."""


def _capture_headers(monkeypatch, module, attr="post"):
    """Record the headers of the next outbound call, then abort it."""
    seen = {}

    def fake(*args, **kwargs):
        seen.update(kwargs.get("headers") or {})
        raise _Captured

    monkeypatch.setattr(module, attr, fake)
    return seen


def test_the_traffic_rollup_post_sends_the_token(monkeypatch):
    import requests

    from lib import satellite_reporter

    seen = _capture_headers(monkeypatch, requests, "post")
    ok, _detail = satellite_reporter.post_rollup(
        {"app": "pannellum", "date": "2026-07-31"}, secret="test-secret"
    )
    assert ok is False  # the fake raised; we only wanted the headers
    assert INTERNAL_UA_TOKEN in seen.get("User-Agent", "")


def test_hub_client_calls_send_the_token(monkeypatch):
    import requests

    from lib import hub_client

    monkeypatch.setenv("CROSS_APP_WEBHOOK_SECRET", "test-secret")
    seen = _capture_headers(monkeypatch, requests, "post")
    assert hub_client._post("/api/agent-key/verify", {"key": "x"}, 1.0) is None
    assert INTERNAL_UA_TOKEN in seen.get("User-Agent", "")


def test_the_ad_fetch_sends_the_token(monkeypatch):
    """One call per docs page view — the loudest of the three."""
    from lib import ad_client

    seen = _capture_headers(monkeypatch, ad_client._session, "get")
    monkeypatch.setattr(ad_client, "_last_failure", 0.0)
    assert ad_client.fetch_ad("/getting-started") is None
    assert INTERNAL_UA_TOKEN in seen.get("User-Agent", "")


@pytest.mark.parametrize("script", ["smoke_live", "audit_links", "network_smoke"])
def test_every_battery_script_sends_the_token(script):
    """A post-deploy battery sweeps every peer; it must not register anywhere."""
    import importlib.util

    from conftest import REPO_ROOT

    spec = importlib.util.spec_from_file_location(
        f"_ua_{script}", REPO_ROOT / "scripts" / f"{script}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    agents = [
        value
        for name, value in vars(module).items()
        if (name == "UA" or name.endswith("_UA")) and isinstance(value, str)
    ]
    assert agents, f"scripts/{script}.py declares no User-Agent constant"
    missing = [ua for ua in agents if INTERNAL_UA_TOKEN not in ua]
    assert missing == [], f"scripts/{script}.py sends untokened UAs: {missing}"


# ------------------------------------------------ the fleet probe convention --
#
# Item 4 of 1.6.44. A PROBE is machinery fetching a network host to check it —
# a workflow's `curl /healthz`, a battery, a link audit, the container's own
# HEALTHCHECK. The convention: a real vendor-or-engine token LEADS, and
# `2plot-internal/probe` follows. The engine token decides the lane; the suffix
# carries INTERNAL_UA_TOKEN, so the write-time drop is what suppresses the row.
# Nothing here trusts that description: the lane table is RE-MEASURED against
# the installed dash_improve_my_llms, because a floor bump is exactly what
# would move it — and on this host the floor is a `>=` line, so the wheel under
# test is not determined by requirements.txt at all.


def test_probe_ua_leads_with_the_engine_and_carries_the_token():
    from lib.constants import PROBE_UA_SUFFIX, probe_ua

    assert PROBE_UA_SUFFIX == f"{INTERNAL_UA_TOKEN}/probe"
    ua = probe_ua("curl/8.7.1")
    assert ua.startswith("curl/8.7.1")
    assert ua.endswith(PROBE_UA_SUFFIX)
    assert INTERNAL_UA_TOKEN in ua


def test_probe_ua_refuses_an_engineless_probe():
    """A UA carrying only the suffix is crawler-lane, whatever it meant.

    That is the defect the convention exists to prevent: an engineless probe
    silently swaps the document out from under a browser-lane assertion.
    """
    from dash_improve_my_llms import classify

    from lib.constants import PROBE_UA_SUFFIX, probe_ua

    for engine in ("", "   ", None):
        with pytest.raises(ValueError):
            probe_ua(engine)

    bare = classify(PROBE_UA_SUFFIX)
    lane = bare["lane"] if isinstance(bare, dict) else bare.lane
    assert lane == "crawler", (
        "the engineless case stopped being crawler-lane — the reason for the "
        f"guard changed, re-read it before relaxing it (got {lane!r})"
    )


@pytest.mark.parametrize(
    "engine,lane,vendor",
    [
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "browser", None),
        ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
         "crawler", "googlebot"),
        ("curl/8.7.1", "crawler", None),
    ],
)
def test_the_suffix_moves_no_lane_no_vendor(engine, lane, vendor):
    """Lane, vendor and bot_type hold BY CONSTRUCTION — measured, not asserted.

    The suppression layer is the tracker's write-time drop. If appending the
    suffix ever moves one of these three, every probe in the fleet is
    measuring a different document than the one it was sent to check, and this
    test is the thing that says so.
    """
    from dash_improve_my_llms import classify

    from lib.constants import probe_ua

    def read(ua):
        r = classify(ua)
        r = r if isinstance(r, dict) else vars(r)
        return (r.get("lane"), r.get("bot_type"), r.get("vendor_key"))

    bare = read(engine)
    probed = read(probe_ua(engine))
    assert bare == probed, f"the suffix moved the classification: {bare} -> {probed}"
    assert bare[0] == lane and bare[2] == vendor, (
        f"the ENGINE token's own classification moved: {bare}"
    )


def _curl_invocations(text: str):
    """Every line that actually invokes curl against a URL, comments dropped.

    Continuations are joined first: the Dockerfile HEALTHCHECK carries its
    `-A` on the line above the URL, and a per-line check would call that a
    bare curl.
    """
    joined, buf = [], ""
    for raw in text.splitlines():
        line = raw.split("#", 1)[0] if raw.strip().startswith("#") else raw
        if not line.strip():
            continue
        buf += " " + line.strip()
        if line.rstrip().endswith("\\"):
            continue
        joined.append(buf.replace("\\", " "))
        buf = ""
    if buf:
        joined.append(buf)
    # NOT filtered on a literal `http://` here, and that cost a revision:
    # cd.yml fetches `"$SITE_URL/healthz"`, so its two curls — the
    # build-match wait and the verify gate, the two most important ones in
    # the fleet — carry no scheme in the source and a scheme filter swept
    # straight past them. Scope is decided by the target instead, below.
    return [ln for ln in joined if "curl " in ln]


# Hosts whose tracker would RECORD the row. The convention is about not
# inflating a 2plot ledger, so it applies to this app (localhost and the
# 127.0.0.1 the workflows boot), to $SITE_URL, and to the network's own
# domains. A tool download from raw.githubusercontent.com is out of scope and
# stays out deliberately: actionlint's installer is not a probe of a network
# host, nothing on the far side counts it, and dressing it as one would put a
# 2plot token in a request to a third party for no benefit.
TRACKED_TARGETS = ("127.0.0.1", "localhost", "$SITE_URL", "2plot.dev", "2plot.ai")


def _fetches_a_tracked_host(call: str) -> bool:
    return any(t in call for t in TRACKED_TARGETS)


def test_every_curl_that_fetches_a_host_sends_a_probe_ua():
    """PER INVOCATION, not per file — and that distinction was earned here.

    The first version of this test asked whether the FILE contained the probe
    suffix anywhere. It passed a mutation that stripped `-A` off ci.yml's boot
    curl AND deleted the workflow's PROBE_UA env, because four other curls in
    the same file still carried it. A sweep that cannot fail on the defect it
    is named for is the "passes on arrival" trap in the kit, so this one asks
    each curl invocation directly.

    The Dockerfile is in scope on the seat's rider: the container HEALTHCHECK
    fetches /healthz every 30s for the life of the process, which is the
    highest-volume internal fetch this host makes.
    """
    from conftest import REPO_ROOT

    targets = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    targets += [REPO_ROOT / "Dockerfile"]

    swept, bare = 0, []
    for path in targets:
        for call in _curl_invocations(path.read_text()):
            if not _fetches_a_tracked_host(call):
                continue
            swept += 1
            if " -A " not in call and "--user-agent" not in call:
                bare.append(f"{path.name}: {call.strip()[:90]}")

    assert swept >= 6, (
        f"only {swept} curl invocations swept across {len(targets)} files — "
        "a sweep that swept nothing is not evidence"
    )
    assert bare == [], "curl invocations with no User-Agent:\n" + "\n".join(bare)


def test_every_script_that_fetches_a_host_carries_the_convention():
    """The Python half: the batteries and the link audit declare their UAs as
    module constants, so the assertion is on the constants."""
    from conftest import REPO_ROOT

    from lib.constants import PROBE_UA_SUFFIX

    scripts = [REPO_ROOT / "scripts" / f"{n}.py"
               for n in ("network_smoke", "smoke_live", "audit_links")]
    missing = [p.name for p in scripts if PROBE_UA_SUFFIX not in p.read_text()]
    assert len(scripts) == 3
    assert missing == [], f"host-fetching scripts with no probe UA: {missing}"


def test_the_probe_caller_tag_never_breaks_the_token_or_the_lane():
    """Same shape as `internal_ua()`'s caller suffix, and the same guarantee.

    The tag is for reading the far side's log; the contract is the token, and
    the lane must not move — a caller tag that reclassified would make the
    battery measure the other document under its own name.
    """
    from dash_improve_my_llms import classify

    from lib.constants import PROBE_UA_SUFFIX, probe_ua

    engine = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    tagged = probe_ua(engine, "network-smoke")
    assert tagged.endswith("network-smoke")
    assert PROBE_UA_SUFFIX in tagged and INTERNAL_UA_TOKEN in tagged
    assert probe_ua(engine, "  ") == probe_ua(engine)
    assert classify(tagged)["lane"] == classify(engine)["lane"] == "browser"
