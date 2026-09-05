"""ONE classifier — the tracker delegates to dash_improve_my_llms.classify().

Until 1.6.34 lib/analytics_tracker.py carried its own User-Agent lists: it
filed ClaudeBot (Anthropic's TRAINING crawler) under "search", still named
the retired `anthropic-ai` / `claude-web` tokens, and counted every UA-less
or library client (httpx, Go-http-client, node-fetch) as a human. Every
host in the fleet reported those numbers to the hub. These pins hold the
delegation in place — each UA string is one taken from the wire on
2026-08-29 — and the last test greps the module so a list cannot come
back quietly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from lib.analytics_tracker import AnalyticsTracker
from lib.constants import INTERNAL_UA_TOKEN

CLAUDEBOT = ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; "
             "ClaudeBot/1.0; +claudebot@anthropic.com)")
GPTBOT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
HTTPX = "python-httpx/0.27.0"
CHROME = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


@pytest.fixture
def tracker(tmp_path, monkeypatch):
    monkeypatch.setenv("ANALYTICS_GEO_LOOKUP", "0")
    return AnalyticsTracker(tmp_path / "ledger.json")


def _rows(tracker):
    tracker.flush()
    path = Path(tracker.data_file)
    if not path.exists():        # nothing written → the file is never created
        return []
    return json.loads(path.read_text())["visits"]


def _one(tracker, ua):
    tracker.track_visit("/", ua, "203.0.113.9")
    rows = _rows(tracker)
    assert len(rows) == 1, rows
    return rows[0]


@pytest.mark.parametrize("ua, bot_type, vendor_key", [
    (CLAUDEBOT, "training", "claudebot"),
    (GPTBOT, "training", "gptbot"),
    (GOOGLEBOT, "traditional", "googlebot"),
    (HTTPX, "unknown", None),
    ("", "unknown", None),
    (None, "unknown", None),
])
def test_crawler_lane_rows(tracker, ua, bot_type, vendor_key):
    assert tracker.is_bot(ua) is True
    assert tracker.detect_bot_type(ua) == bot_type
    row = _one(tracker, ua)
    assert row["device_type"] == "bot"
    assert row["bot_type"] == bot_type
    assert row["vendor_key"] == vendor_key
    assert row["lane"] == "crawler"
    assert row["verified"] in ("verified", "unverified", "n/a")


def test_claudebot_is_training_and_unverifiable(tracker):
    """The finding that produced this file: ClaudeBot was 'search' for a
    year. And Anthropic publishes no IP ranges, so `verified` is n/a — a
    property of the vendor, never a defect on this host."""
    row = _one(tracker, CLAUDEBOT)
    assert row["bot_type"] == "training"
    assert row["vendor_class"] == "training"
    assert row["verified"] == "n/a"


def test_a_browser_row_carries_no_vendor_keys(tracker):
    """Human rows carry no vendor identity — the rollup's tests depend on it.

    THE KEY SET MOVED AT 1.6.44 item 16, and this assertion moving with it is
    the item landing rather than a test being relaxed. `visitor_key` is new
    and `ip_address` left the default set: the address is resolved so one
    visitor can be told from another, then reduced to a keyed one-way hash.
    The next test asserts the address is genuinely absent, so widening this
    set here cannot hide its return.
    """
    assert tracker.is_bot(CHROME) is False
    row = _one(tracker, CHROME)
    assert row["device_type"] == "desktop"
    assert set(row) <= {"timestamp", "path", "device_type", "user_agent",
                        "visitor_key", "ip_address", "location"}, row
    for vendor_field in ("bot_type", "vendor_key", "vendor_class", "verified"):
        assert vendor_field not in row, vendor_field


def test_a_default_config_visit_row_carries_no_ip_address(tracker):
    """Item 16's acceptance, and the half that the widened set above needs.

    Without this, adding `visitor_key` to the permitted keys would also have
    permitted `ip_address` to sit there forever.
    """
    row = _one(tracker, CHROME)
    assert "ip_address" not in row, (
        "a raw client address reached the ledger under the default config"
    )
    assert row["visitor_key"], "no visitor_key — visitors cannot be told apart"
    assert len(row["visitor_key"]) == 16


def test_internal_traffic_is_still_dropped_before_classification(tracker):
    tracker.track_visit("/", f"Mozilla/5.0 {INTERNAL_UA_TOKEN}-sweep", "203.0.113.9")
    assert _rows(tracker) == []


def test_the_module_carries_no_user_agent_list():
    """The grep. A token the registry lacks is a pushback to the package,
    never a list here (.claude/CLAUDE.md trap)."""
    src = (Path(__file__).resolve().parent.parent / "lib" / "analytics_tracker.py").read_text()
    code = "\n".join(
        line for line in src.splitlines()
        if not line.lstrip().startswith("#")
    )
    # Strip the module docstring — it names the old tokens to explain why
    # they are gone; the assertion is about CODE.
    code = re.sub(r'^"""[\s\S]*?"""', "", code, count=1)
    survivors = [t for t in ("'anthropic-ai'", "'claude-web'", "'perplexitybot'",
                             "'gptbot'", "'claudebot'", "'googlebot'", "'bingbot'",
                             "'headlesschrome'", "'phantomjs'", "'pingdom'")
                 if t in code]
    assert survivors == [], f"a hand-written UA list is back: {survivors}"
    assert "from dash_improve_my_llms import classify" in src


# ---------------------------------- item 8: prefer, then derive (1.6.44) --


def test_the_packages_vendor_class_passes_through_untouched():
    """A CONFLICTING fixture, or the test cannot fail.

    "prefer" that never derives and "derive" that never prefers both pass a
    one-sided test, so the package's answer here is deliberately one the
    registry would NOT give: if the fork ever recomputes unconditionally,
    this value changes and the assertion says so.
    """
    import lib.analytics_tracker as mod

    calls = []

    def fake_classify(ua, ip=None):
        return {"lane": "crawler", "bot_type": "training",
                "vendor_key": "gptbot", "vendor_class": "a-class-only-the-"
                                                        "package-knows",
                "verified": "n/a"}

    def fake_registry(vendor_key):
        calls.append(vendor_key)
        return "training"

    original_classify = mod.classify
    original_registry = mod._vendor_class_from_registry
    mod.classify = fake_classify
    mod._vendor_class_from_registry = fake_registry
    try:
        result = mod._classify("anything")
    finally:
        mod.classify = original_classify
        mod._vendor_class_from_registry = original_registry

    assert result["vendor_class"] == "a-class-only-the-package-knows", (
        "the fork overwrote the package's own vendor_class"
    )
    assert calls == [], (
        "the registry was consulted while the package had already answered"
    )


def test_the_registry_is_consulted_only_where_the_class_is_absent():
    """The mirror direction. Both are needed: see the docstring above."""
    import lib.analytics_tracker as mod

    calls = []

    def fake_classify(ua, ip=None):
        return {"lane": "crawler", "bot_type": "training",
                "vendor_key": "gptbot", "vendor_class": None,
                "verified": "n/a"}

    def fake_registry(vendor_key):
        calls.append(vendor_key)
        return "derived-from-the-registry"

    original_classify = mod.classify
    original_registry = mod._vendor_class_from_registry
    mod.classify = fake_classify
    mod._vendor_class_from_registry = fake_registry
    try:
        result = mod._classify("anything")
    finally:
        mod.classify = original_classify
        mod._vendor_class_from_registry = original_registry

    assert calls == ["gptbot"], "the registry was never asked"
    assert result["vendor_class"] == "derived-from-the-registry"


def test_the_registry_helper_reads_the_packages_registry_not_a_local_map():
    """No hand-written table. This repo lost a year to one."""
    from lib.analytics_tracker import _vendor_class_from_registry

    assert _vendor_class_from_registry(None) is None
    assert _vendor_class_from_registry("") is None
    # An unknown key must be None rather than a guess.
    assert _vendor_class_from_registry("not-a-real-vendor-key-xyz") is None
    # A real one answers, and the answer agrees with classify()'s.
    from dash_improve_my_llms import classify

    c = classify("Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)")
    if c.get("vendor_key") and c.get("vendor_class"):
        assert _vendor_class_from_registry(c["vendor_key"]) == c["vendor_class"], (
            "the registry and the classifier disagree — they must be one source"
        )


def test_where_this_hosts_null_classes_actually_came_from():
    """The correction this item forced, pinned so it is not re-derived.

    The fleet note reads "`vendor_class` ARRIVES ON THE EVENT at 2.9.2", and
    a reader takes that to mean classify() withholds it below 2.9.2. It does
    not: at the wheel resolved here, classify() returns vendor_class and
    EVENT_FIELDS does not carry the key at all. The null classes came from
    the read-event path dropping it at the app boundary — a different surface
    and a different fix.

    If a future wheel adds vendor_class to EVENT_FIELDS this goes red, which
    is the signal to re-read the comment in _vendor_class_from_registry, not
    a failure.
    """
    from dash_improve_my_llms import classify
    from dash_improve_my_llms._ledger import EVENT_FIELDS

    c = classify("Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)")
    has_on_classification = c.get("vendor_class") is not None
    has_on_event = "vendor_class" in EVENT_FIELDS
    assert has_on_classification or has_on_event, (
        "neither surface carries vendor_class — the derive branch is now the "
        "only path and its docstring is stale"
    )


# ------------------------- privacy by design (1.6.44 item 16) --


def test_the_tracker_makes_no_outbound_request_of_any_kind():
    """PARSED, not grepped — and the spec's own detect had to be corrected
    for exactly this reason.

    The drop's first form was "no `ip-api` string in lib/", which CANNOT pass
    on a tree that DOCUMENTS the removal: this module now carries a paragraph
    naming ip-api.com and explaining that the lookup is gone, so the grep
    matches the documentation of the absence it is hunting. The parsed form
    asks the imports and the definitions instead.
    """
    import ast

    from conftest import REPO_ROOT

    tree = ast.parse((REPO_ROOT / "lib" / "analytics_tracker.py").read_text())

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert imported, "parsed no imports at all — the AST read swept nothing"
    for network in ("requests", "urllib", "http", "socket", "httpx", "aiohttp"):
        assert network not in imported, (
            f"the tracker imports {network} — it can reach the network again"
        )

    defined = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert defined, "parsed no definitions at all"
    for gone in ("_geolocate", "geo_for", "get_geolocation", "_backfill_geo"):
        assert gone not in defined, f"{gone} came back"


def test_the_lookup_was_removed_not_defaulted_off():
    """A disabled lookup is one environment variable away from an enabled
    one, which is why the switch is gone with the code."""
    import ast

    from conftest import REPO_ROOT

    tree = ast.parse((REPO_ROOT / "lib" / "analytics_tracker.py").read_text())
    literals = {node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert "ANALYTICS_GEO_LOOKUP" not in literals, (
        "the geo-lookup switch is still read — the path it gates is what "
        "item 16 removed"
    )


def test_location_is_whatever_the_edge_sent_and_nothing_more():
    """Item 16's acceptance, all three shapes."""
    from lib.analytics_tracker import header_geo

    full = header_geo({"CF-IPCountry": "GB", "CF-IPCity": "Manchester",
                       "CF-Region": "England", "CF-IPLatitude": "53.48",
                       "CF-IPLongitude": "-2.24"})
    assert full["country"] == "GB" and full["city"] == "Manchester"
    assert full["region"] == "England" and full["latitude"] == "53.48"

    country_only = header_geo({"CF-IPCountry": "us"})
    assert country_only == {"country": "US", "country_code": "US"}, country_only

    assert header_geo({}) == {}
    assert header_geo(None) == {}
    # XX (unknown) and T1 (Tor) are not countries.
    assert header_geo({"CF-IPCountry": "XX"}) == {}
    assert header_geo({"CF-IPCountry": "T1"}) == {}


def test_a_visit_with_no_headers_carries_no_location_at_all(tracker):
    row = _one(tracker, CHROME)
    assert "location" not in row


def test_the_visitor_key_is_keyed_and_one_way(monkeypatch):
    """HMAC, not a bare digest. The IPv4 space is small enough to enumerate,
    so an unkeyed hash of an address is a reversible encoding of it."""
    import lib.analytics_tracker as mod

    monkeypatch.setenv("ANALYTICS_VISITOR_SALT", "salt-one")
    a = mod.visitor_key("203.0.113.9", CHROME)
    monkeypatch.setenv("ANALYTICS_VISITOR_SALT", "salt-two")
    b = mod.visitor_key("203.0.113.9", CHROME)
    assert a != b, "the salt does not key the hash — it is a bare digest"

    monkeypatch.setenv("ANALYTICS_VISITOR_SALT", "salt-one")
    assert mod.visitor_key("203.0.113.9", CHROME) == a, "not deterministic"
    assert mod.visitor_key("203.0.113.10", CHROME) != a
    assert mod.visitor_key("203.0.113.9", "other-ua") != a
    assert "203.0.113.9" not in a and len(a) == 16


def test_the_salt_is_gitignored_in_the_same_commit_that_creates_it():
    """A committed salt makes every visitor_key this host writes computable
    by anyone with the repo, which undoes the item entirely."""
    from conftest import REPO_ROOT

    ignore = (REPO_ROOT / ".gitignore").read_text()
    assert ".visitor_salt" in ignore
    # And it must not already be tracked.
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".visitor_salt"],
        cwd=REPO_ROOT, capture_output=True, text=True)
    assert tracked.returncode != 0, "the salt is committed — rotate it"


def test_the_rollup_prefers_the_stored_key_and_falls_back():
    """Both directions. Without the fallback, every row written before this
    release collapses to its User-Agent and the session counts either side of
    the deploy stop being comparable."""
    from lib.traffic_rollup import visitor_key as rollup_key

    new_row = {"visitor_key": "abc123def456", "user_agent": CHROME}
    assert rollup_key(new_row) == "abc123def456"

    old_row = {"ip_address": "203.0.113.9", "user_agent": CHROME}
    legacy = rollup_key(old_row)
    assert legacy.startswith("203.0.113.9|"), legacy
    assert rollup_key({"user_agent": CHROME}).startswith("?|")

    # Two different old rows must not collide, which is the failure the
    # fallback prevents.
    other = rollup_key({"ip_address": "203.0.113.10", "user_agent": CHROME})
    assert other != legacy


def test_healthz_says_which_location_headers_this_host_has_seen():
    """The Cloudflare transform is an owner click PER ZONE, so the only
    honest answer is the set of headers that have actually turned up."""
    from lib.analytics_tracker import geo_headers_seen, header_geo
    from lib.health import health_payload

    header_geo({"CF-IPCountry": "GB", "CF-IPCity": "Manchester"})
    seen = geo_headers_seen()
    assert "cf-ipcountry" in seen and "cf-ipcity" in seen
    assert seen == sorted(seen)

    block = health_payload("flask").get("geo")
    if block is not None:
        assert "cf-ipcity" in block["headers_seen"]
