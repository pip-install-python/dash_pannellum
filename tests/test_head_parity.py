"""HEAD answers wherever GET answers, on the lane this host actually serves.

Template 1.6.44 item 2, INVERTED on this fork. The item asks forks to retire
``HeadAsGetMiddleware`` on the strength of dash-improve-my-llms 2.9.4's
route-level HEAD. This tree never had the middleware — so the item's detect
("the middleware present with no recorded reason") could not fire, and the
absence read as a deliberate retirement rather than as drift. It was drift:
the template's own docstring for the class names the hosts the defect was
measured on, and one of them is this repo.

Measured here at dimll 2.8.0 before the port: 11 of 15 pairs matched.
``/healthz`` answered 405 to HEAD on all three UAs — the path the 2plot.ai
hub sweeps hourly, and the default probe method of most uptime monitors —
and ``/`` answered 405 to a browser UA while answering 200 to a crawler one,
because the package's prerender replies above the router. That split is why
a single-UA HEAD check reads green on a broken host.

Retirement is gated on the PIN, not the calendar. When this fork's
requirements line moves to ``==2.9.4`` at 1.6.45, re-run this file with the
middleware disabled and expect 15/15 before deleting anything.
"""
import pytest

from conftest import backend

# The five paths whose whole job is to be fetched by something that may
# preflight with HEAD, plus the two the hub and the monitors use.
PATHS = ["/healthz", "/llms.txt", "/robots.txt", "/sitemap.xml", "/"]

# Three UAs because this app serves TWO DOCUMENTS. `/` to a crawler is the
# package's prerender, `/` to a browser is Dash's catch-all, and only the
# second one 405s — a parity check on one UA proves nothing about the other.
UAS = {
    "browser": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 "
                "Safari/537.36"),
    "crawler": ("Mozilla/5.0 (compatible; Googlebot/2.1; "
                "+http://www.google.com/bot.html)"),
    "probe": "curl/8 2plot-internal/probe",
}


def _pairs(client):
    for path in PATHS:
        for label, ua in UAS.items():
            get = client.get(path, ua)
            head = client.head(path, ua)
            yield path, label, get.status, head.status


def test_head_matches_get_on_every_path_and_every_ua(client):
    if backend() != "fastapi":
        pytest.skip("Werkzeug derives HEAD from every GET rule; only the "
                    "ASGI lane can have this defect")

    mismatches = [
        f"{path} ({label}): GET {g} but HEAD {h}"
        for path, label, g, h in _pairs(client)
        if g != h
    ]
    assert mismatches == [], (
        "HEAD/GET parity broken on the lane this host serves in production:\n"
        + "\n".join(mismatches)
    )


def test_the_shim_is_registered_outermost():
    """Non-vacuity, half one: the class is actually in the stack.

    Without this, a parity pass from a run that never had the middleware —
    or never removed it — is worth nothing. This round's own measurement is
    the evidence: 11/15 without, 15/15 with.
    """
    if backend() != "fastapi":
        pytest.skip("ASGI lane only")

    from lib.asgi_middleware import HeadAsGetMiddleware, register_asgi_middleware

    registered = []

    class _FakeServer:
        def add_middleware(self, cls, **_kw):
            registered.append(cls)

    class _FakeApp:
        server = _FakeServer()

    register_asgi_middleware(_FakeApp())
    assert HeadAsGetMiddleware in registered
    assert registered[-1] is HeadAsGetMiddleware, (
        "Starlette runs the LAST-added middleware outermost — registered "
        "before the tracker, the prerender answers `/` first and the "
        "browser-lane 405 survives"
    )


def test_the_shims_retirement_is_gated_on_the_pin_not_the_date():
    """Half two: the reason survives the next sync.

    A future round WILL arrive asking this fork to retire the class, exactly
    as 1.6.44 did. The gate is the requirements line, and a reader who meets
    "retire" without meeting "below 2.9.4 it is load-bearing" will delete a
    shim that is still holding `/healthz` up.
    """
    from conftest import REPO_ROOT

    src = (REPO_ROOT / "lib" / "asgi_middleware.py").read_text()
    flat = " ".join(src.split())
    assert "GATED ON THE PIN, NOT THE CALENDAR" in flat
    assert "2.9.4" in flat, "the version IS the whole content of the claim"
