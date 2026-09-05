"""The ledger's boot guard — 1.6.44 item 22.

BOOTED IN A SUBPROCESS, not asserted through caplog, and that is the item's
own correction to the drop: the warning is a `print` at IMPORT time, which
caplog cannot see at all, and mirroring the existing `[visibility]` line is
the whole point — an operator greps ONE deploy log for both.

Pairs with item 20. The guard says it once at boot; `/healthz`'s
`ledger.persistent` says it continuously. The last test here asserts the two
AGREE rather than pinning either value on its own, which is what item 22
asks for.
"""
import os
import subprocess
import sys

from conftest import REPO_ROOT

BOOT = "import sys; sys.path.insert(0, '.'); import lib.analytics_tracker"


def _boot(env_overrides):
    env = dict(os.environ)
    env.pop("TRAFFIC_ANALYTICS_FILE", None)
    env.update({k: v for k, v in env_overrides.items() if v is not None})
    return subprocess.run([sys.executable, "-c", BOOT], cwd=REPO_ROOT,
                          capture_output=True, text=True, env=env)


def test_an_unset_ledger_path_warns_at_boot():
    """The failure this exists for: analytics_path() falls back SILENTLY to
    the repository root, which is the container filesystem and is replaced
    wholesale on every deploy."""
    result = _boot({})
    assert result.returncode == 0, result.stderr
    assert "[analytics] WARNING" in result.stdout
    assert "TRAFFIC_ANALYTICS_FILE unset" in result.stdout
    assert "will not survive a deploy" in result.stdout


def test_a_configured_ledger_path_is_SILENT(tmp_path):
    """Both directions, or the warning is a constant rather than a guard."""
    result = _boot({"TRAFFIC_ANALYTICS_FILE": str(tmp_path / "ledger.json")})
    assert result.returncode == 0, result.stderr
    assert "[analytics] WARNING" not in result.stdout, result.stdout


def test_a_var_path_that_is_not_a_mount_warns_too():
    """The second failure mode, and the quieter one: an app can mkdir a path
    under /var and everything works until the deploy that replaces the
    filesystem."""
    result = _boot({"TRAFFIC_ANALYTICS_FILE": "/var/not-a-real-mount/led.json"})
    assert result.returncode == 0, result.stderr
    assert "[analytics] WARNING" in result.stdout
    assert "not a mounted disk" in result.stdout


def test_it_mirrors_the_visibility_warning_it_sits_beside():
    """An operator greps ONE deploy log. Two stores that fail for identical
    reasons must not announce it in two different shapes.

    On this host the `[visibility] WARNING` line has been the ONLY acceptance
    check for whether the declared disk is really mounted, and it is
    owner-only because it lives in a deploy log nobody else can read.
    """
    visibility = (REPO_ROOT / "lib" / "page_visibility.py").read_text()
    analytics = (REPO_ROOT / "lib" / "analytics_tracker.py").read_text()

    assert "[visibility] WARNING" in visibility
    assert "[analytics] WARNING" in analytics
    for shared in ("not a mounted disk", "Blueprint sync"):
        assert shared in visibility, f"the visibility warning lost {shared!r}"
        assert shared in analytics, f"the ledger warning does not mirror {shared!r}"


def test_the_boot_guard_and_the_healthz_block_agree(monkeypatch, tmp_path):
    """Item 22's pairing rule, asserted as an AGREEMENT rather than a value.

    The guard warns exactly when `ledger.persistent` would read False. Pinning
    either one alone would let them drift into contradicting each other on the
    same host, which is worse than having neither.
    """
    import lib.analytics_tracker as tracker_mod
    from lib.health import health_payload

    # Outside the repo root: persistent True, and the guard is silent when
    # the variable is what put it there.
    outside = tmp_path / "ledger.json"
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: outside)
    assert health_payload("flask")["ledger"]["persistent"] is True
    assert "[analytics] WARNING" not in _boot(
        {"TRAFFIC_ANALYTICS_FILE": str(outside)}).stdout

    # Inside the repo root: persistent False, and the guard warns.
    inside = REPO_ROOT / "visitor_analytics.json"
    monkeypatch.setattr(tracker_mod, "analytics_path", lambda: inside)
    assert health_payload("flask")["ledger"]["persistent"] is False
    assert "[analytics] WARNING" in _boot({}).stdout
