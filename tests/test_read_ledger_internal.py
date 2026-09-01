"""The READ table drops internal traffic too (sync 1.6.43 item 1, note 83a).

"Counted nowhere" includes the read table. Until this landed, the
network's own probes — the hub's hourly health sweep, this repo's link
audit, every post-deploy battery — were written into `reads` and were the
busiest "vendor" on the board. `track_visit` had dropped them since the
internal-traffic contract existed; `record_read`, added with the 2.8.0
floor, never learned the rule.

THREE THINGS THIS FILE REFUSES TO ASSUME, each of which is a way the fix
could be a silent no-op:

1. THE FIELD NAME. `EVENT_FIELDS` calls it `ua`, not `user_agent`. A drop
   keyed on the wrong name drops nothing and every test below still
   passes if written carelessly — so the name is asserted against the
   installed package, not trusted.
2. THE NEGATIVE. A test that finds zero rows and a test that wrote zero
   rows are the same green. Both directions are asserted in the same
   test, and the counts are printed beside the result.
3. THE VERSION. The resolved `dash-improve-my-llms` is printed, because
   the suite's version and production's can differ and this drop keys on
   a field the package owns.
"""

from __future__ import annotations

import json

from lib.constants import INTERNAL_UA, INTERNAL_UA_TOKEN


def _resolved_dimll() -> str:
    from importlib.metadata import version

    return version("dash-improve-my-llms")


def test_event_fields_names_the_ua_field_ua(capsys):
    """The drop keys on `ua`. If a package version renames it, this fails
    HERE with the name in hand, rather than in production as silence."""
    from dash_improve_my_llms._ledger import EVENT_FIELDS

    with capsys.disabled():
        print(f"\n    dash-improve-my-llms resolved: {_resolved_dimll()}")
        print(f"    EVENT_FIELDS: {list(EVENT_FIELDS)}")
    assert "ua" in EVENT_FIELDS, (
        "record_read keys the internal-traffic drop on `ua`; this package "
        f"version does not have that field: {list(EVENT_FIELDS)}"
    )
    assert "user_agent" not in EVENT_FIELDS, (
        "if the field were `user_agent`, the drop as written is a no-op"
    )


def _event(ua: str) -> dict:
    """A read event shaped like the package's, with a CURRENT timestamp so
    the retention window keeps it."""
    import time

    from dash_improve_my_llms._ledger import EVENT_FIELDS

    ev = {k: None for k in EVENT_FIELDS}
    ev.update(ts=time.time(), path="/llms.txt", tier="index", lane="crawler",
              bot_type="training", vendor_key="gptbot", verified="n/a",
              verdict="served", status=200, bytes=500, ua=ua)
    return ev


def test_internal_reads_are_dropped_and_real_ones_are_kept(tmp_path, capsys):
    """BOTH DIRECTIONS, in one test, with the counts printed.

    A pin that only asserted "no internal rows" would pass just as well on
    a `record_read` that dropped everything — which is why the real vendor
    row is asserted in the same breath.

    UA convention (ops, 2026-09-01): a probe carrying a vendor token is
    written as vendor-token + the internal token, never a bare vendor UA,
    because a bare one writes an unverified vendor row into a real ledger.
    """
    from lib.analytics_tracker import AnalyticsTracker

    ledger = tmp_path / "a.json"
    t = AnalyticsTracker(ledger)

    internal_probe = f"Mozilla/5.0 (compatible; GPTBot/1.2) {INTERNAL_UA}"
    real_crawler = ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; "
                    "compatible; GPTBot/1.2; +https://openai.com/gptbot)")

    t.record_read(_event(internal_probe))
    t.record_read(_event(real_crawler))
    t.flush()

    rows = json.loads(ledger.read_text()).get("reads", [])
    uas = [r.get("ua") or "" for r in rows]
    internal_rows = [u for u in uas if INTERNAL_UA_TOKEN in u.lower()]

    with capsys.disabled():
        print(f"\n    dash-improve-my-llms resolved: {_resolved_dimll()}")
        print(f"    reads rows written: {len(rows)}  (expected 1)")
        print(f"    rows carrying the internal token: {len(internal_rows)}  (expected 0)")

    assert len(internal_rows) == 0, (
        f"{len(internal_rows)} internal-traffic row(s) reached the read "
        "table — the network counts its own probes as vendor reads"
    )
    assert len(rows) == 1, (
        f"expected exactly 1 kept row, got {len(rows)} — a drop that removes "
        "everything satisfies the negative above while destroying the table"
    )
    assert "gptbot" in (rows[0].get("ua") or "").lower()


def test_the_drop_precedes_the_row_build():
    """Source pin: the token check must come BEFORE any field is read, as
    it does in track_visit. A check placed after the row is built still
    passes the behavioural tests above but does needless work per event on
    the request path — and, more importantly, records the shape of the
    contract rather than one of its consequences."""
    import inspect

    from lib.analytics_tracker import AnalyticsTracker

    src = inspect.getsource(AnalyticsTracker.record_read)
    body = src.split('"""', 2)[-1]  # past the docstring
    token_at = body.find("INTERNAL_UA_TOKEN")
    build_at = body.find("EVENT_FIELDS")
    assert token_at != -1, "record_read never learned the internal-traffic rule"
    assert build_at != -1, "record_read no longer builds the row from EVENT_FIELDS"
    assert token_at < build_at, (
        "the internal-traffic drop must precede the row build"
    )


def test_a_bare_missing_ua_is_not_treated_as_internal(tmp_path):
    """An absent UA is the crawler lane since 2.8.0, not internal traffic.
    `(event.get("ua") or "")` must not turn None into a drop."""
    from lib.analytics_tracker import AnalyticsTracker

    ledger = tmp_path / "b.json"
    t = AnalyticsTracker(ledger)
    ev = _event("")
    ev["ua"] = None
    t.record_read(ev)
    t.flush()
    rows = json.loads(ledger.read_text()).get("reads", [])
    assert len(rows) == 1, "a UA-less read is a crawler read, not internal traffic"
