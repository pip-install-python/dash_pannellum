"""The app keeps the row — on_document_read → AnalyticsTracker.record_read.

dash-improve-my-llms 2.8.0 emits one event per corpus document it serves
and does no I/O with it. Before 1.6.34 nothing here listened, so tier,
verified, verdict, bytes and policy were discarded at the app boundary
exactly as the package used to discard them internally. These pins drive
the REAL app (conftest's client) and read the ledger file back.
"""

from __future__ import annotations

import json
import time
import warnings
from pathlib import Path


from conftest import BROWSER_UA

GPTBOT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"


def _reads(app_module):
    from lib.analytics_tracker import tracker

    tracker.flush()
    path = Path(tracker.data_file)
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("reads") or []


def _new_reads(app_module, before):
    return _reads(app_module)[len(before):]


def test_one_llms_txt_fetch_writes_exactly_one_read_row(app_module, client):
    before = _reads(app_module)
    r = client.get("/llms.txt", user_agent=GPTBOT)
    assert r.status == 200
    rows = _new_reads(app_module, before)
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["kind"] == "read"
    assert row["path"] == "/llms.txt"
    assert row["tier"] == "index"
    assert row["lane"] == "crawler"
    assert row["bot_type"] == "training"
    assert row["vendor_key"] == "gptbot"
    # In-process the test client carries NO client address, so the package
    # cannot check GPTBot's published ranges and says n/a; on the wire
    # (behind Cloudflare) the same request is verified/unverified. The
    # drop expected only the latter pair — the tree says the triple.
    assert row["verified"] in ("verified", "unverified", "n/a")
    assert row["verdict"] == "served"
    assert row["status"] == 200
    assert row["bytes"] > 0
    assert "client_ip" not in row, "ANALYTICS_KEEP_CLIENT_IP is off by default"
    assert row["ua"] == GPTBOT[:160]
    # policy is None until dimll 2.8.1 writes it; the rollup groups it as
    # "default". The KEY is present regardless (EVENT_FIELDS is fixed).
    assert "policy" in row


def test_a_browser_page_view_writes_no_read_row(app_module, client):
    """The package emits for the crawler document only (measured on the
    2.8.0 wheel by the ops seat); a Chrome GET / is the browser lane."""
    before = _reads(app_module)
    assert client.get("/", user_agent=BROWSER_UA).status == 200
    assert _new_reads(app_module, before) == []


def test_the_hook_is_registered_exactly_once(app_module):
    """Tests import run.py more than once per process and on_document_read
    appends; a second import must not double-write."""
    from dash_improve_my_llms import _ledger

    from lib.analytics_tracker import tracker

    assert _ledger._callbacks.count(tracker.record_read) == 1
    assert getattr(tracker, "_read_hook_registered", False) is True


def test_a_raising_writer_never_touches_the_response(app_module, client):
    """The package's fail-open: the writer raising is warned about, the
    document still goes out. Assert the warning, not silence."""
    from dash_improve_my_llms import _ledger

    def boom(event):
        raise RuntimeError("ledger disk is gone")

    _ledger._callbacks.append(boom)
    _ledger._warned.clear()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = client.get("/llms.txt", user_agent=GPTBOT)
        assert r.status == 200 and len(r.text) > 200
        msgs = [str(w.message) for w in caught if "on_document_read" in str(w.message)]
        assert msgs, "the package should warn once about a raising callback"
        assert "ledger disk is gone" in msgs[0]
    finally:
        _ledger._callbacks.remove(boom)
        _ledger._warned.clear()


def test_record_read_keeps_client_ip_only_when_asked(tmp_path, monkeypatch):
    from lib import analytics_tracker as at

    ev = {k: None for k in at.EVENT_FIELDS}
    # a CURRENT ts: the reads table shares the visits' retention window
    ev.update(ts=time.time(), path="/llms.txt", tier="index", client_ip="203.0.113.9")

    t = at.AnalyticsTracker(tmp_path / "a.json")
    t.record_read(ev)
    t.flush()
    row = json.loads((tmp_path / "a.json").read_text())["reads"][0]
    assert "client_ip" not in row and row["kind"] == "read"

    monkeypatch.setattr(at, "KEEP_CLIENT_IP", True)
    t2 = at.AnalyticsTracker(tmp_path / "b.json")
    t2.record_read(ev)
    t2.flush()
    row = json.loads((tmp_path / "b.json").read_text())["reads"][0]
    assert row["client_ip"] == "203.0.113.9"


def test_a_pre_1_6_34_ledger_gains_reads_without_losing_visits(tmp_path):
    from lib.analytics_tracker import AnalyticsTracker, EVENT_FIELDS

    p = tmp_path / "old.json"
    p.write_text(json.dumps({"visits": [{"timestamp": "2099-01-01T00:00:00",
                                         "path": "/", "device_type": "desktop",
                                         "user_agent": "x"}],
                             "stats": {"total": 1}}))
    t = AnalyticsTracker(p)
    ev = {k: None for k in EVENT_FIELDS}
    ev.update(ts=4_000_000_000.0, path="/llms.txt", tier="index")
    t.record_read(ev)
    t.flush()
    data = json.loads(p.read_text())
    assert len(data["visits"]) == 1 and len(data["reads"]) == 1


# --------------------- reads are never pruned by count (1.6.44 item 21) --


def _read_row(days_ago, i):
    from datetime import datetime, timedelta

    ts = (datetime.now() - timedelta(days=days_ago)).timestamp()
    return {"ts": ts, "path": f"/p{i}/llms.txt", "kind": "read",
            "verdict": "served", "ua": "Mozilla/5.0 (compatible; GPTBot/1.2)"}


def test_reads_keep_every_row_inside_the_window_and_drop_the_dated_one():
    """Item 21's acceptance, at the exact boundary.

    20,001 read rows inside the retention window plus one outside: 20,001
    must remain and the dated one must be gone. The cap is 20,000, so a
    corpus one row over is the smallest one that can tell the two rules
    apart.
    """
    from lib.analytics_tracker import MAX_VISITS, _prune, _read_stamp

    assert MAX_VISITS == 20000, (
        f"the cap moved to {MAX_VISITS}; this corpus is sized against it"
    )
    rows = [_read_row(1, i) for i in range(MAX_VISITS + 1)]
    rows.append(_read_row(3650, 999999))          # far outside the window

    kept = _prune(rows, stamp=_read_stamp, cap=False)
    assert len(kept) == MAX_VISITS + 1, len(kept)
    assert all(r["path"] != "/p999999/llms.txt" for r in kept), (
        "the dated row survived — the retention window is not being applied"
    )


def test_the_same_corpus_pruned_WITH_the_cap_loses_an_in_window_row():
    """PROVE THE TEST RED on the pre-item behaviour before believing it.

    The item says so explicitly, and it is the difference between a test that
    measures the fix and a test that would have passed before it. With
    cap=True the same corpus loses a row the retention window says should
    still be there — which is the defect, reproduced.
    """
    from lib.analytics_tracker import MAX_VISITS, _prune, _read_stamp

    rows = [_read_row(1, i) for i in range(MAX_VISITS + 1)]
    rows.append(_read_row(3650, 999999))

    capped = _prune(rows, stamp=_read_stamp, cap=True)
    assert len(capped) == MAX_VISITS, len(capped)
    # And the row it lost is the OLDEST in-window one — the ledger eating its
    # own history first.
    assert capped[0]["path"] != "/p0/llms.txt", (
        "the cap did not drop from the front; re-read _prune before trusting "
        "either direction of this pair"
    )


def test_visits_KEEP_the_count_cap():
    """The mirror. "reads prune by date" that also stopped capping visits
    would be a different change, and a one-sided test cannot tell them
    apart."""
    from datetime import datetime, timedelta

    from lib.analytics_tracker import MAX_VISITS, _prune

    stamp = (datetime.now() - timedelta(days=1)).isoformat()
    visits = [{"timestamp": stamp, "path": f"/{i}"}
              for i in range(MAX_VISITS + 5)]
    assert len(_prune(visits)) == MAX_VISITS


def test_the_call_site_is_source_pinned_per_table():
    """SOURCE-pinned by AST, per the item's own note.

    The choice of rule per table lives at the CALL, and a behavioural test
    cannot see a `cap=True` restored above it — the corpus that would catch
    it is 20,001 rows, and nobody writes that test twice.
    """
    import ast

    from conftest import REPO_ROOT

    tree = ast.parse((REPO_ROOT / "lib" / "analytics_tracker.py").read_text())
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_prune"]
    assert len(calls) == 2, f"{len(calls)} _prune call sites, expected 2"

    by_table = {}
    for call in calls:
        kwargs = {kw.arg: kw.value for kw in call.keywords}
        stamp = getattr(kwargs.get("stamp"), "id", "_visit_stamp")
        cap = kwargs.get("cap")
        by_table[stamp] = None if cap is None else cap.value

    assert by_table.get("_read_stamp") is False, (
        "the reads call site does not pass cap=False — reads are being "
        "pruned by count again"
    )
    assert by_table.get("_visit_stamp", "default") in (None, True), (
        "the visits call site stopped capping"
    )
