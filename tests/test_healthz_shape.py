"""The `/healthz` payload's shape, and the lane that was narrowing it.

Template 1.6.44 items 1 and 20, built here as one commit on the seat's
rider — because on THIS host they are one defect. Production runs
``DASH_BACKEND=fastapi``, so the typed route in ``lib/asgi_routes.py`` is
the one the hub sweeps, and a pydantic ``response_model`` drops every field
it does not declare IN SILENCE. ``llms_version`` was therefore going to land
in ``health_payload`` and never reach this host's wire — measured by the ops
seat at 03:14Z on 2026-09-05: ``"llms_version" in json`` → False.

The guard below is written for the CLASS, not for the two keys that
happened to be missing: every key ``health_payload`` produces must reach the
wire on whichever lane answers.
"""
import json

import pytest


# --------------------------------------------------------- item 1: the version


def test_llms_version_is_the_resolved_package_version():
    """Resolved by IMPORT, never read from requirements.txt.

    The whole point of the field is that a `>=` line does not determine what
    a cached Docker layer installed.
    """
    import dash_improve_my_llms as pkg

    from lib.health import health_payload

    assert health_payload("flask")["llms_version"] == pkg.__version__


def test_llms_version_is_omitted_not_invented_when_the_import_fails(monkeypatch):
    """A health payload that invents a version is worse than a silent one."""
    import builtins

    import lib.health as health_mod

    real_import = builtins.__import__

    def _boom(name, *args, **kwargs):
        if name == "dash_improve_my_llms":
            raise ImportError("simulated")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _boom)
    assert "llms_version" not in health_mod._llms_version()


# ----------------------------------------------------- item 20: the ledger


def test_the_ledger_block_has_its_four_keys_and_their_types():
    from lib.health import health_payload

    ledger = health_payload("flask")["ledger"]
    assert set(ledger) == {"path", "persistent", "visits", "reads"}
    assert isinstance(ledger["persistent"], bool)
    assert isinstance(ledger["visits"], int)
    assert isinstance(ledger["reads"], int)
    assert ledger["path"] is None or isinstance(ledger["path"], str)


def test_persistent_is_measured_from_the_path_not_declared(monkeypatch, tmp_path):
    """BOTH directions, so the boolean cannot pass as a constant.

    This host's render.yaml declares
    ``TRAFFIC_ANALYTICS_FILE=/var/data/visitor_analytics.json`` against a
    disk, and that declaration has never been verifiable from a session —
    Blueprint env applies only on a sync. leaflet ran for weeks with a
    declared disk and no disk. A blueprint's declaration is an intention;
    this reports the filesystem.
    """
    import lib.analytics_tracker as tracker_mod
    from conftest import REPO_ROOT
    from lib.health import health_payload

    outside = tmp_path / "ledger.json"
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: outside)
    assert health_payload("flask")["ledger"]["persistent"] is True

    inside = REPO_ROOT / "visitor_analytics.json"
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: inside)
    assert health_payload("flask")["ledger"]["persistent"] is False, (
        "a path under the app tree is the container filesystem, whatever "
        "the blueprint says"
    )


def test_a_missing_ledger_is_zeros_and_not_an_error(monkeypatch, tmp_path):
    """/healthz must stay 200. A diagnostic that can take the health probe
    down with it is a liability."""
    import lib.analytics_tracker as tracker_mod
    from lib.health import health_payload

    monkeypatch.setattr(tracker_mod, "analytics_path",
                        lambda: tmp_path / "nothing-here.json")
    payload = health_payload("flask")
    assert payload["ok"] is True
    assert payload["ledger"]["visits"] == 0 and payload["ledger"]["reads"] == 0
    assert payload["ledger"]["path"].endswith("nothing-here.json")


def test_a_corrupt_ledger_is_zeros_and_not_an_error(monkeypatch, tmp_path):
    import lib.analytics_tracker as tracker_mod
    from lib.health import health_payload

    broken = tmp_path / "half-written.json"
    broken.write_text('{"visits": [{"path": "/a"}')
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: broken)
    payload = health_payload("flask")
    assert payload["ok"] is True
    assert payload["ledger"]["visits"] == 0


def test_the_counts_are_the_rows_of_the_file_the_tracker_writes(
        monkeypatch, tmp_path):
    import lib.analytics_tracker as tracker_mod
    from lib.health import health_payload

    ledger = tmp_path / "a.json"
    ledger.write_text(json.dumps({
        "visits": [{"path": "/a"}, {"path": "/b"}, {"path": "/c"}],
        "reads": [{"path": "/llms.txt"}],
    }))
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: ledger)
    block = health_payload("flask")["ledger"]
    assert (block["visits"], block["reads"]) == (3, 1)


def test_the_block_never_carries_row_contents(monkeypatch, tmp_path):
    """Counts, a boolean and a path. Nothing about a visitor."""
    import lib.analytics_tracker as tracker_mod
    from lib.health import health_payload

    ledger = tmp_path / "a.json"
    ledger.write_text(json.dumps({
        "visits": [{"path": "/secret", "user_agent": "SECRET-UA",
                    "visitor_key": "deadbeefdeadbeef"}],
        "reads": [],
    }))
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: ledger)
    serialised = json.dumps(health_payload("flask")["ledger"])
    for leaked in ("SECRET-UA", "deadbeefdeadbeef", "/secret"):
        assert leaked not in serialised


# ------------------------------------------- the lane guard (items 1 + 20)


def test_the_existing_keys_are_still_there(client):
    """Both blocks are ADDITIVE; a RENAME is still the failure."""
    body = json.loads(client.get("/healthz").text)
    for key in ("ok", "backend", "dash_version", "python", "app", "reporting",
                "ledger"):
        assert key in body, f"/healthz lost {key}"


def test_the_serving_lane_serves_every_key_the_payload_builds(client):
    """The guard for the CLASS, not for the two keys that were missing.

    This is the assertion that would have caught the live defect: on the
    FastAPI lane — the one this host serves — ``HealthResponse`` silently
    dropped ``llms_version`` from the moment it landed, and the docstring on
    that class already WARNED about exactly this failure while the class was
    committing it. Prose describing a trap does not prevent the trap; this
    does.
    """
    from lib.backend import get_backend_info
    from lib.health import health_payload

    lane = get_backend_info().name
    served = json.loads(client.get("/healthz").text)
    expected = health_payload(lane)

    missing = sorted(set(expected) - set(served))
    assert missing == [], (
        f"the {lane} lane's /healthz drops {missing} — a response_model that "
        "narrows the payload is the two-lanes trap with a type annotation "
        "on it"
    )


def test_the_asgi_model_keeps_keys_it_does_not_know_about():
    """Belt to the test above: the NEXT additive key must survive without
    anyone remembering to declare it here."""
    pytest.importorskip("fastapi", reason="the ASGI model needs fastapi, "
                                          "which the flask legs do not install")
    from lib.asgi_routes import HealthResponse

    widened = HealthResponse(backend="fastapi", dash_version="4.4.1",
                             python="3.14.7", a_future_key="kept")
    assert widened.model_dump().get("a_future_key") == "kept", (
        "an undeclared key is dropped — declare extra='allow'"
    )


# ------------------------------------- item 1: the three openapi_* knobs


def test_the_openapi_knobs_are_wired_from_this_repos_constants():
    """Identity flows ONE way — from lib/constants, never guessed.

    Read structurally from run.py rather than from a booted app, because
    what is asserted is the WIRING: without these the FastAPI lane's OpenAPI
    document is titled "FastAPI" version "0.1.0", and on this host that is
    what an agent discovering the site through /openapi.json reads as the
    app's name.
    """
    import ast

    from conftest import REPO_ROOT

    tree = ast.parse((REPO_ROOT / "run.py").read_text())
    wired = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "update":
            for kw in node.keywords:
                if kw.arg and kw.arg.startswith("openapi_"):
                    wired[kw.arg] = kw.value
    assert set(wired) == {"openapi_title", "openapi_description",
                          "openapi_version"}, wired
    # title and description come from constants; version is a literal, and
    # deliberately so — it is the API SURFACE's version, not the package's.
    assert "SITE_SHORT_NAME" in ast.dump(wired["openapi_title"])
    assert isinstance(wired["openapi_description"], ast.Name)
    assert wired["openapi_description"].id == "SITE_DESCRIPTION"
    assert isinstance(wired["openapi_version"], ast.Constant)


def test_the_knobs_are_guarded_by_what_the_installed_package_accepts():
    """This fork's divergence from the template, and it must not rot.

    The template pinned `==2.9.4` in item 1's own commit and could pass the
    kwargs unconditionally. The 1.6.44 seat rider holds this host at
    `>=2.8.0`, and `LLMSConfig` at 2.8.0 takes NO `openapi_*` kwarg — an
    unconditional call is a TypeError at import time on whichever wheel a
    cached Docker layer happens to hold. Both directions are asserted, so
    the guard cannot pass as a constant.
    """
    from conftest import REPO_ROOT

    src = (REPO_ROOT / "run.py").read_text()
    assert "_llms_config_accepts(\"openapi_title\")" in src

    namespace = {}
    exec(compile(
        src[src.index("def _llms_config_accepts"):src.index("\n\n\n", src.index(
            "def _llms_config_accepts"))],
        "<guard>", "exec"), namespace)
    guard = namespace["_llms_config_accepts"]

    class _Old:
        def __init__(self, warn_missing_llms_doc=True):
            pass

    class _New:
        def __init__(self, warn_missing_llms_doc=True, openapi_title=None):
            pass

    namespace["LLMSConfig"] = _Old
    assert guard("openapi_title") is False, "a 2.8.0-shaped config must say no"
    namespace["LLMSConfig"] = _New
    assert guard("openapi_title") is True, "a 2.9.4-shaped config must say yes"
