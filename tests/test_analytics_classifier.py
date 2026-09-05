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
    """Human rows are byte-for-byte what v3 wrote — the rollup's tests must
    not move on adoption."""
    assert tracker.is_bot(CHROME) is False
    row = _one(tracker, CHROME)
    assert row["device_type"] == "desktop"
    assert set(row) <= {"timestamp", "path", "device_type", "user_agent",
                        "ip_address", "location"}, row


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
