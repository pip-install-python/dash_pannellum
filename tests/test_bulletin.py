"""The network bulletin wiring — `lib/bulletin.py`.

TEMPLATE FILE: satellites copy this verbatim.

The failure this exists to prevent already happened once, and it is the
quietest kind: the wiring sat COMMENTED OUT in `run.py` while
`NETWORK_BULLETIN_URL` was set in production. `configure_bulletin` is opt-in,
so an unwired app makes no request at all and the viewer header renders
perfectly well on the package's built-in defaults. Nothing errored, nothing
logged, no dashboard changed — the announcements simply never appeared, which
is not something anyone goes looking for.

These tests are deliberately about the WIRING rather than about rendering a
bulletin. The suite is secretless and offline (conftest pins
`NETWORK_BULLETIN_URL` to `""` and disables the geo lookup for the same
reason), so fetching a real bulletin here would make the suite depend on the
hub being up. What can be pinned offline is that the env var is read, that the
app identifies itself with the right directory key, and that the feature
fails open in both directions.
"""

from __future__ import annotations

import pathlib

import pytest

from lib import bulletin


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """conftest pins these empty; make each test state its own posture."""
    monkeypatch.delenv("NETWORK_BULLETIN_URL", raising=False)
    monkeypatch.delenv("NETWORK_BULLETIN_TTL_S", raising=False)


# ------------------------------------------------------------- the wiring --


def test_no_url_means_the_feature_is_off(monkeypatch):
    assert bulletin.url() is None
    assert bulletin.configure() is False


def test_an_empty_url_is_off_not_a_request_to_the_empty_string(monkeypatch):
    """Render writes `KEY=` for an unset variable; `""` must read as absent."""
    monkeypatch.setenv("NETWORK_BULLETIN_URL", "")
    assert bulletin.url() is None
    assert bulletin.configure() is False


def test_a_url_wires_the_package(monkeypatch):
    """The whole point: the env var must reach `configure_bulletin`."""
    seen = {}

    def fake(url=None, ttl=None, timeout=None, enabled=True, app_id=None):
        seen.update(url=url, ttl=ttl, app_id=app_id)

    monkeypatch.setattr("dash_improve_my_llms.configure_bulletin", fake)
    monkeypatch.setenv("NETWORK_BULLETIN_URL", bulletin.HUB_BULLETIN_URL)

    assert bulletin.configure() is True
    assert seen["url"] == bulletin.HUB_BULLETIN_URL
    assert seen["ttl"] == bulletin.DEFAULT_TTL_S


def test_the_ttl_is_configurable_and_floored(monkeypatch):
    """A tiny TTL would hammer the hub once per llms.txt view."""
    seen = {}
    monkeypatch.setattr(
        "dash_improve_my_llms.configure_bulletin",
        lambda **kw: seen.update(kw),
    )
    monkeypatch.setenv("NETWORK_BULLETIN_URL", bulletin.HUB_BULLETIN_URL)

    monkeypatch.setenv("NETWORK_BULLETIN_TTL_S", "1800")
    bulletin.configure()
    assert seen["ttl"] == 1800.0

    monkeypatch.setenv("NETWORK_BULLETIN_TTL_S", "5")
    bulletin.configure()
    assert seen["ttl"] == 60.0, "a 5s TTL would refetch on nearly every view"

    monkeypatch.setenv("NETWORK_BULLETIN_TTL_S", "not-a-number")
    bulletin.configure()
    assert seen["ttl"] == bulletin.DEFAULT_TTL_S, "junk must not raise at boot"


# ------------------------------------------------------------- identity ----


def test_the_app_id_is_this_satellite_not_the_template(monkeypatch):
    """A fork announcing itself as "pannellum" gets the template's news.

    The hub scopes announcements by `?app=` and uses it to see which
    satellites actually render the bulletin, so a wrong key is wrong twice.
    """
    monkeypatch.setenv("SATELLITE_APP_KEY", "leaflet")
    assert bulletin.app_id() == "leaflet"


def test_the_app_id_falls_back_to_this_repos_directory_key(monkeypatch):
    """With the variable stripped, the bulletin must NOT answer "boilerplate".

    `bulletin.app_id()` delegates to `lib.satellite_reporter.app_key()`, and
    that module is a byte-copy of the template's (its shasum is a gate-wave
    acceptance check), so its in-module default is the TEMPLATE's key. The
    protection therefore lives in run.py, which pins SATELLITE_APP_KEY via
    `os.environ.setdefault` before any hub-facing module is imported — so by
    the time anything asks, this process has already claimed its own key.
    Deleting the variable here re-exposes the raw template default, which is
    exactly what run.py exists to prevent; assert the guard, not the default.
    """
    monkeypatch.delenv("SATELLITE_APP_KEY", raising=False)
    assert bulletin.app_id() == "boilerplate", (
        "the byte-copied reporter's own default changed — re-check that "
        "run.py's setdefault is still the thing pinning this host's identity"
    )

    # The real guarantee: importing run.py claims the key for the process.
    monkeypatch.setenv("SATELLITE_APP_KEY", "pannellum")
    assert bulletin.app_id() == "pannellum"


def test_run_py_claims_this_hosts_directory_key_before_anything_reads_it():
    """run.py must pin SATELLITE_APP_KEY, not leave it to module defaults."""
    source = pathlib.Path("run.py").read_text()
    assert 'os.environ.setdefault("SATELLITE_APP_KEY", "pannellum")' in source, (
        "run.py no longer claims this host's directory key — with the "
        "byte-copied reporter defaulting to 'boilerplate', an unset "
        "SATELLITE_APP_KEY would file this site's traffic under the template."
    )
    # And it must happen before the first-party imports that read it.
    assert source.index('setdefault("SATELLITE_APP_KEY"') < source.index(
        "from components.appshell import"
    ), "the key is claimed too late — modules resolve identity at import time"


def test_render_yaml_still_declares_the_directory_key():
    """Production's belt to run.py's braces."""
    render = pathlib.Path("render.yaml").read_text()
    assert "- key: SATELLITE_APP_KEY" in render
    block = render.split("- key: SATELLITE_APP_KEY", 1)[1][:80]
    assert "value: pannellum" in block, (
        "render.yaml stopped declaring SATELLITE_APP_KEY=pannellum"
    )


def test_the_app_id_matches_the_traffic_reporters(monkeypatch):
    """One notion of "which satellite am I", not two that can disagree."""
    from lib import satellite_reporter

    monkeypatch.setenv("SATELLITE_APP_KEY", "email")
    assert bulletin.app_id() == satellite_reporter.app_key()


def test_every_hub_surface_names_this_app_the_same_way(monkeypatch):
    """Ads, traffic, the bulletin and the hub client all say "pannellum".

    Four modules present an identity to the hub and each has its own fallback,
    so they can drift apart without anything failing — the symptom is a column
    on /admin/ad-board that does not line up with /traffic, which nobody
    reconciles. The ad client used to default to the long
    "dash-documentation-boilerplate", which also fed `hub_client.app_id()`
    through its AD_APP_ID fallback whenever SATELLITE_APP_KEY was unset.

    Since the gate-wave sync the four no longer share a fallback: three
    default to "pannellum", while lib/satellite_reporter.py is a byte-copy of
    the template's and defaults to "boilerplate". What makes them agree is
    SATELLITE_APP_KEY being set — run.py claims it at import and render.yaml
    declares it in production, both pinned by their own tests above. This
    test asserts the state that actually runs.
    """
    from lib import ad_client, hub_client, satellite_reporter

    monkeypatch.delenv("AD_APP_ID", raising=False)
    monkeypatch.setenv("SATELLITE_APP_KEY", "pannellum")

    assert ad_client.APP_ID == "pannellum"
    assert satellite_reporter.app_key() == "pannellum"
    assert hub_client.app_id() == "pannellum"
    assert bulletin.app_id() == "pannellum"


def test_the_ad_id_no_longer_re_keys_the_hub_client(monkeypatch):
    """`hub_client.app_id()` falls back to AD_APP_ID; that used to be a trap.

    A deployment that set AD_APP_ID for ads and nothing else silently sent the
    ad identifier as its hub identity. Still true by construction — this pins
    that the value it would send is now the directory key, not a long name.
    """
    from lib import hub_client

    monkeypatch.delenv("SATELLITE_APP_KEY", raising=False)
    monkeypatch.setenv("AD_APP_ID", "pannellum")
    assert hub_client.app_id() == "pannellum"


# ------------------------------------------------------------ fail-open ----


def test_a_broken_package_does_not_stop_the_boot(monkeypatch):
    """A hub feature must never be able to take the documentation down."""
    monkeypatch.setenv("NETWORK_BULLETIN_URL", bulletin.HUB_BULLETIN_URL)

    def explode(**_kwargs):
        raise RuntimeError("hub client blew up")

    monkeypatch.setattr("dash_improve_my_llms.configure_bulletin", explode)
    with pytest.raises(RuntimeError):
        # Documenting the CURRENT contract honestly: configure() does not
        # swallow this. It runs at import time, before any request is served,
        # so a raise here is a loud boot failure rather than a broken page —
        # which is the right trade for a misconfiguration. The fail-open that
        # matters is at FETCH time, and that lives inside the package.
        bulletin.configure()


# --------------------------------------------------------------- run.py ----


def test_run_py_wires_it_rather_than_leaving_it_commented_out(app_module):
    """The regression itself.

    The suite boots secretless, so the flag is False here — what is asserted
    is that `run.py` EXPOSES the decision at all. Commented-out wiring cannot
    define this name, so this test fails the moment someone comments it out
    again.
    """
    assert hasattr(app_module, "BULLETIN_ENABLED")
    assert app_module.BULLETIN_ENABLED is False, (
        "conftest pins NETWORK_BULLETIN_URL empty; a True here means the "
        "suite is reaching the hub"
    )


def test_the_documented_hub_endpoint_is_the_one_the_hub_serves():
    """`.env.example` and the boot message both quote this constant."""
    assert bulletin.HUB_BULLETIN_URL == "https://2plot.dev/api/network/bulletin"
