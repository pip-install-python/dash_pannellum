"""Run the network battery against the in-process app.

`scripts/network_smoke.py` only ever executes in two places a developer never
watches: against the container CI just booted, and against production after a
deploy. That is exactly the code that rots — a typo in a check turns it into a
silent pass and the battery keeps reporting green over a broken host.

So it runs here too, with its `fetch` pointed at the test client. Three
distinct things get proven, and it is worth being explicit about which:

1. the battery's own logic still works (the checks fire, and they can fail);
2. this app satisfies every check the network standard makes of a satellite;
3. the per-site block at the top of the script — the expected H1, the hidden
   paths — still matches the app it describes.

What it cannot prove is the deployed artifact, which is the whole reason the
container run and the post-deploy run exist as well.
"""

from __future__ import annotations

import importlib.util
import sys

import pytest

from conftest import REPO_ROOT
from lib.constants import BASE_URL, INTERNAL_UA_TOKEN, SITE_BRAND

BASE = BASE_URL


@pytest.fixture(scope="module")
def battery():
    spec = importlib.util.spec_from_file_location(
        "network_smoke", REPO_ROOT / "scripts" / "network_smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["network_smoke"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def wired(battery, client, monkeypatch):
    """Point the battery's `fetch` at the test client.

    The signature is `fetch(url, ua=..., method=..., body=..., headers=...)`
    and it returns `(status, lowercased_headers, text)`. Only GET is used by
    the satellite battery, so a non-GET here is a bug in the script rather
    than something to emulate.
    """
    seen_agents = []

    def fetch(url, ua=battery.UA, method="GET", body=None, headers=None,
              timeout=None, retries=1):
        assert method == "GET", f"the satellite battery issued a {method}"
        seen_agents.append(ua)
        path = url[len(BASE):] if url.startswith(BASE) else url
        accept = (headers or {}).get("Accept")
        response = client.get(path or "/", user_agent=ua, accept=accept)
        return response.status, dict(response.headers), response.text

    monkeypatch.setattr(battery, "fetch", fetch)
    monkeypatch.setattr(battery, "_RESULTS", [])
    # No declaration in the in-process seat: here the "host" serves from the
    # suite's own interpreter, which on the matrix's window legs (3.13/3.12)
    # is deliberately not the fleet Python. The python_matches_declared
    # check still proves the field EXISTS; holding the artifact to the
    # Dockerfile's minor is the container and production seats' job.
    monkeypatch.setattr(battery, "declared_python_minor", lambda: None)
    battery.seen_agents = seen_agents
    return battery


def test_the_battery_passes_against_this_app(wired, capsys):
    wired.satellite_checks(BASE)
    output = capsys.readouterr().out

    failed = [(name, detail) for name, verdict, detail in wired._RESULTS
              if verdict == wired.FAIL]
    assert failed == [], f"battery failures against the in-process app:\n{output}"
    assert len(wired._RESULTS) >= 9, "checks silently stopped running"


def test_every_request_the_battery_makes_is_internal(wired):
    """A battery that pollutes the ledger it is auditing is worse than none."""
    wired.satellite_checks(BASE)
    untokened = [ua for ua in wired.seen_agents if INTERNAL_UA_TOKEN not in ua]
    assert untokened == [], f"battery sent untokened User-Agents: {untokened}"


def test_the_expected_h1_tracks_the_brand_constant(battery):
    """The per-site block is a copy of `SITE_BRAND`; copies drift."""
    assert battery.SITE_H1 == f"# {SITE_BRAND}"


def test_the_battery_reports_a_failure_rather_than_swallowing_it(wired):
    """The check that keeps every other assertion here honest.

    If `check()` ever caught too broadly, the battery would print `pass` for a
    host that is on fire. Break one expectation on purpose and require it to
    be reported.
    """
    wired.SITE_H1 = "# not this site"
    try:
        wired.satellite_checks(BASE)
    finally:
        wired.SITE_H1 = f"# {SITE_BRAND}"

    verdicts = {name: verdict for name, verdict, _ in wired._RESULTS}
    assert verdicts.get("llms_txt_identity") == wired.FAIL


def test_the_default_base_url_matches_the_container_port(battery):
    """CI boots the image and runs the battery with no --base-url."""
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    port = battery.DEFAULT_BASE_URL.rsplit(":", 1)[1]
    assert f"EXPOSE {port}" in dockerfile, (
        f"the battery defaults to port {port}; the image exposes something else"
    )
    # Render injects PORT, so the CMD binds ${PORT:-<default>} — the default
    # must still match the battery's port (same shape as dash-email's image).
    assert f":${{PORT:-{port}}}" in dockerfile, "the CMD binds a different port"


def test_network_smoke_urlopens_pass_the_ssl_context():
    """Source pin: EVERY urlopen in network_smoke.py must carry
    context=SSL_CONTEXT.

    Same class as the pin in tests/test_smoke_live.py, same reason it needs
    a SOURCE pin rather than a wired one: every test here monkeypatches
    `fetch`, so no behavioural test can ever see the handshake. This script
    RAISES after its retries, so on a Python without OS trust-store
    integration (macOS — the seat the fleet's F4 battery sweeps from) the
    first https probe aborted the whole run and a perfectly healthy
    satellite read as down. Linux CI verifies fine and never shows it.
    """
    import re

    source = (REPO_ROOT / "scripts" / "network_smoke.py").read_text()
    calls = re.findall(r"urlopen\((?:[^)]|\n)*?\)", source)
    assert calls, "no urlopen calls found in network_smoke.py — probe rewritten?"
    naked = [c for c in calls if "context=SSL_CONTEXT" not in c]
    assert not naked, (
        f"urlopen without context=SSL_CONTEXT in network_smoke.py: {naked} — "
        "on macOS this dies in the handshake and reads as a dead host"
    )


def test_the_batterys_default_ua_is_browser_lane_and_still_internal():
    """Sync item 17 (muischeduler's finding): at dimll >= 2.8 a UA without a
    browser engine token is crawler-lane, so a default-UA check reads the
    crawler document. The default names the browser lane FIRST and keeps
    the internal token (a substring match) so the tracker still drops it;
    CRAWLER_UA stays the other lane."""
    from dash_improve_my_llms import classify

    from lib.constants import INTERNAL_UA_TOKEN
    from scripts import network_smoke as ns

    assert classify(ns.UA)["lane"] == "browser"
    assert ns.UA.startswith("Mozilla/5.0") and "AppleWebKit" in ns.UA
    assert INTERNAL_UA_TOKEN in ns.UA and ns.UA.endswith("network-smoke")
    assert classify(ns.CRAWLER_UA)["lane"] == "crawler"
    assert INTERNAL_UA_TOKEN in ns.CRAWLER_UA


def test_smoke_live_default_ua_is_browser_lane_too():
    """Item 17 says AUDIT the other tool rather than assume it. This host's
    scripts/smoke_live.py already had the right shape — engine token first,
    internal token after — and this pin is what keeps it that way."""
    from dash_improve_my_llms import classify

    from lib.constants import INTERNAL_UA_TOKEN
    from scripts import smoke_live as sl

    assert classify(sl.BROWSER_UA)["lane"] == "browser"
    assert INTERNAL_UA_TOKEN in sl.BROWSER_UA
    assert classify(sl.CRAWLER_UA)["lane"] == "crawler"


def test_every_hidden_page_has_its_llms_twin_in_the_battery(app_module):
    """The census rule, enforced instead of asked for.

    `HIDDEN_DOC_PATHS` says a page joins it in the same change that hides
    it. That was prose until now, and prose is how `/analytics/llms.txt`
    outlived its page by four weeks (deleted in ac6c33f) while
    `/admin/traffic` — added with the read ledger — was never swept at all.
    Derived from the package's own hidden set, so a new mark_hidden call
    fails here rather than going unmeasured on the wire.
    """
    from dash_improve_my_llms import is_hidden

    import dash

    from scripts.network_smoke import HIDDEN_DOC_PATHS

    hidden = [p["path"] for p in dash.page_registry.values()
              if is_hidden(p["path"])]
    assert hidden, "no hidden pages registered — this pin would be vacuous"
    for path in hidden:
        twin = path.rstrip("/") + "/llms.txt"
        assert twin in HIDDEN_DOC_PATHS, (
            f"{path} is mark_hidden but {twin} is not in "
            "scripts/network_smoke.HIDDEN_DOC_PATHS — the live battery "
            "never checks that its llms.txt is silent"
        )


def test_the_battery_sweeps_no_path_whose_page_is_gone(app_module):
    """The other half: a path in the list whose page no longer exists passes
    vacuously — a 404 because nothing is there, not because it is hidden.
    `/admin/llms.txt` is the deliberate exception, the prefix canary."""
    import dash

    from scripts.network_smoke import HIDDEN_DOC_PATHS

    CANARIES = {"/admin/llms.txt"}
    paths = {p["path"] for p in dash.page_registry.values()}
    for doc in HIDDEN_DOC_PATHS:
        if doc in CANARIES:
            continue
        page = doc[: -len("/llms.txt")]
        assert page in paths, (
            f"{doc} is swept but {page} is not registered — the check "
            "passes because the page is GONE, not because it is hidden"
        )
