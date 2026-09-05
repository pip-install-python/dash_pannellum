"""
ASGI/Starlette middleware ports of Flask-only hooks used in this boilerplate.

When the Dash backend is FastAPI, these slot in where the Flask
``before_request`` decorator was used.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from lib.analytics_tracker import tracker


class HeadAsGetMiddleware:
    """Answer ``HEAD`` wherever ``GET`` is served (template 1.6.32).

    HTTP requires it, Werkzeug derives it from every ``GET`` rule for free,
    and FastAPI does not: a route declared ``@router.get(...)`` answers
    ``405 Method Not Allowed`` to ``HEAD``.

    LANDING HERE AT 1.6.44 RATHER THAN 1.6.32, AND THAT IS THE FINDING.
    The template's own docstring for this class names the hosts it was
    measured on — "measured on pannellum and muischeduler, 2026-08-27" —
    and pannellum is THIS repo. The shim was written because of a defect
    observed here and it was never ported; twelve template releases later
    item 2 arrived asking forks to RETIRE it, and the detect ("the
    middleware present with no recorded reason") cannot fire on a tree that
    never received it. An absent mechanism and a deliberately removed one
    look identical to every detect in the drop.

    MEASURED HERE BEFORE PORTING, fastapi lane, in-process, dimll 2.8.0 —
    5 paths x 3 UAs, HEAD status vs GET status:
        /healthz      browser/crawler/probe   GET 200  HEAD 405   x3
        /             browser                 GET 200  HEAD 405
        /llms.txt, /robots.txt, /sitemap.xml  all 9 pairs matched
        /             crawler, probe          matched
      => 11/15 without this class. `/healthz` is the path the 2plot.ai hub
      sweeps hourly and the default probe method of most uptime monitors,
      and this host runs DASH_BACKEND=fastapi in production. The kit's
      "probe with GET, not HEAD" trap has been standing in for this fix.

    `/` answering 405 to a browser UA and 200 to a crawler UA is the shape
    that hid the defect three times upstream: the 200 is the package's
    prerender replying ABOVE the router, so any single-UA HEAD check reads
    green. Two lanes, two documents — again.

    Why middleware and not ``methods=["GET", "HEAD"]`` on the declarations:
    this tree declares only two of the affected surfaces. ``/llms.txt``,
    ``/<page>/llms.txt``, ``/robots.txt`` and ``/sitemap.xml`` are
    registered by dash-improve-my-llms' own FastAPI adapter, and ``/`` by
    Dash's page catch-all — ``dash/backends/_fastapi.py::add_url_rule``
    calls ``add_api_route(..., methods=methods or ["GET"])``, and nothing in
    this repo or in the package can declare methods on those. The fix has to
    sit above the router. Pure ASGI rather than ``BaseHTTPMiddleware`` so it
    neither buffers the response nor breaks streaming.

    RETIREMENT IS GATED ON THE PIN, NOT THE CALENDAR (item 2's own words).
    dash-improve-my-llms 2.9.4 walks the router and adds HEAD wherever GET
    is allowed, Dash's lifespan-registered catch-all included; at that
    version the template measured 15/15 without this class and retired it.
    This fork's requirements line is held at ``>=2.8.0`` by the 1.6.44 seat
    rider until the fleet pin lands at 1.6.45, and 2.8.0 is what this venv
    resolves — so the shim is load-bearing here. Delete it in the same
    commit that pins ``==2.9.4``, and re-measure the fifteen pairs before
    believing the deletion, with the disable proved non-vacuous.

    The re-dispatch is a full ``GET``: same status, same headers, same work.
    The body is dropped here so the response is empty at every layer under
    test — on the wire h11 already frames a HEAD response as content-length
    0 and never writes those bytes, which is why the Quart lane needs
    nothing and gets nothing.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http" or scope.get("method") != "HEAD":
            await self.app(scope, receive, send)
            return

        sent_body = False

        async def send_without_body(message) -> None:
            nonlocal sent_body
            if message["type"] != "http.response.body":
                await send(message)
                return
            # A streaming handler emits many body messages; exactly one
            # empty, final message goes out or the server raises on the
            # message after the response completed.
            if sent_body:
                return
            sent_body = True
            await send({"type": "http.response.body", "body": b"",
                        "more_body": False})

        await self.app({**scope, "method": "GET"}, receive, send_without_body)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Track every request through the analytics tracker.

    Mirrors the Flask ``before_request`` shim in ``run.py``. Failures are
    silently swallowed — analytics should never block a real response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            client = request.client
            ip = client.host if client else None
            # Headers carry the real client IP/country behind a proxy or CDN;
            # request.client is the last hop (the proxy) in production.
            tracker.track_visit(
                request.url.path,
                request.headers.get("user-agent", ""),
                ip,
                headers=dict(request.headers),
            )
        except Exception:
            pass
        return await call_next(request)


class StaticCacheMiddleware(BaseHTTPMiddleware):
    """Give ``/assets/`` a cache lifetime (1.6.44 item 6g).

    The ASGI half of the Flask ``after_request`` in ``run.py``; the policy
    itself lives in ``lib/static_cache`` so the two lanes cannot drift into
    serving different lifetimes for the same file.

    THIS IS THE LANE THAT SERVES on this host — production runs
    ``DASH_BACKEND=fastapi``, so a fix proven only on the Flask
    ``after_request`` would be a fix nobody visiting the site receives. Both
    halves ship together and a test asserts both exist.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        from lib.static_cache import cache_control_for

        value = cache_control_for(request.url.path)
        if value and response.status_code == 200:
            response.headers["Cache-Control"] = value
        return response


def register_asgi_middleware(app) -> None:
    """Attach all ASGI middleware to ``app.server`` (a FastAPI instance).

    Order matters: Starlette runs the LAST-added middleware outermost, so
    ``HeadAsGetMiddleware`` goes on after the tracker and a HEAD becomes a
    GET before anything else — the package's bot middleware and its
    prerender included — sees the request. Registered the other way round,
    the prerender answers `/` first and the browser-lane 405 survives.
    """
    app.server.add_middleware(AnalyticsMiddleware)
    app.server.add_middleware(StaticCacheMiddleware)
    app.server.add_middleware(HeadAsGetMiddleware)
