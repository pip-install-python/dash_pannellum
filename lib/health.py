"""
``/healthz`` liveness probe for the Flask and Quart backends.

The 2plot.ai hub sweeps every satellite's ``/healthz`` once an hour and records
up/down + latency — that's the "Satellite health & reach" panel on ``/traffic``
(the traffic rollup this app POSTs supplies the other half). The FastAPI build
declares a typed ``/healthz`` in ``lib/asgi_routes`` so it shows up in Swagger,
but it renders from the SAME ``health_payload`` below — one payload builder on
every backend, so the probe contract doesn't depend on which backend a
deployment happens to run. That matters here more than on most hosts: this
site runs ``DASH_BACKEND=fastapi`` in production, so the typed route IS the
one the hub actually sweeps.

Keep it cheap: the hub measures the round trip, so any work done here is
reported back as this app being slow.
"""
from __future__ import annotations

import os

import dash


def reporting_enabled() -> bool:
    """Whether the rollup can actually POST (the HMAC secret is set).

    lib/satellite_reporter.py is a BYTE-COPY of the boilerplate's (its
    shasum against the template is an acceptance check), and the template
    dropped this helper — the boilerplate's own /healthz doesn't publish a
    `reporting` field, so upstream had no use for it. This host does publish
    it, so the predicate lives here instead of reaching into the reporter's
    private `_secret()`: importing a private name across a module we are
    contractually required to re-copy verbatim would break silently on the
    next sync. One env read, same semantics.
    """
    return bool(os.getenv("CROSS_APP_WEBHOOK_SECRET"))


def _resolved_country() -> str:
    """``geo.explain_resolution`` over THIS request's headers, or a reason.

    Reads the framework's request object directly rather than anything the
    package threads through, so it answers "did the country header reach this
    app at all?" independently of how the enforcement seam is wired.
    """
    try:
        from dash_improve_my_llms import geo
        from dash_improve_my_llms._headers import normalize_headers
    except Exception:
        return "unavailable (pre-2.7.0 package)"

    try:
        from flask import has_request_context, request

        if not has_request_context():
            return "no request context"
        return geo.explain_resolution(normalize_headers(request.headers))
    except Exception:
        return "unavailable"


def health_payload(backend: str) -> dict:
    payload = {"ok": True, "backend": backend, "dash_version": dash.__version__}

    # Which commit the RUNNING instance was built from. This is what lets CD
    # verify the artifact it shipped rather than whichever build happens to
    # be serving: a Render service with a disk restarts with a blip instead
    # of overlapping instances, so a bare 200 proves nothing about WHICH
    # build answered (the muicharts finding, 2026-08-21 — its battery had
    # been verifying the previous release on every run, invisibly, until a
    # new surface made the race lose). Optional on purpose: omitted where
    # the platform variable does not exist, so the fleet's probe contract
    # is unchanged.
    build = os.environ.get("RENDER_GIT_COMMIT")
    if build:
        payload["build"] = build

    # WHICH satellite answered. `build` says which commit, this says which
    # app — and on a fleet where every host shares this template and a
    # hostname can be repointed between services (llms.2plot.dev was,
    # 2026-08-23), "is this the site I think it is?" is a different question
    # from "is this the build I shipped?".
    #
    # Read straight from the environment rather than through
    # satellite_reporter.app_key(): that helper is byte-copied from the
    # template and so falls back to "boilerplate", which on this host would
    # be a LIE in the one field whose whole job is saying who answered.
    # run.py claims SATELLITE_APP_KEY via os.environ.setdefault before any
    # hub-facing import, so in practice this is the same value the reporter
    # sends — which is the property that matters, because a mis-set key
    # overwrites another app's analytics rows on the hub (the flows deploy
    # once reported as "email", found via exactly this field).
    payload["app"] = os.environ.get("SATELLITE_APP_KEY") or "unknown"

    # Whether the hourly rollup can actually POST. Not in the template's
    # payload — this host added it, and the fleet battery asserts on it.
    payload["reporting"] = reporting_enabled()

    # The geo guardrail's LIVE state (dash-improve-my-llms >= 2.7.0). Added
    # after llms-2plot-dev's production verification could not answer "is
    # the denylist actually in force?" from outside: the control board and
    # the public policy showcase both showed countries denied while every
    # request was served 200, and the only surfaces that could settle it
    # (the boot log, the operator panel) need credentials a verification
    # pass does not have.
    #
    # Counts and flags only — never the denylist's country codes: a health
    # endpoint is not where anyone should learn policy. `resolved` reveals
    # only the caller's own country back to them, which Cloudflare's
    # /cdn-cgi/trace already does — and it is THE per-host check
    # docs/GEO.md calls mandatory before trusting a denylist. It also
    # localises a failure: geo can be configured with a full denylist and
    # still never match if the country header is not reaching the app —
    # "configured: true, denied: 7, resolved: unknown" says that in one
    # line.
    try:
        from dash_improve_my_llms import geo
    except ImportError:
        # Pre-2.7 package: the key is OMITTED, not error-flagged — a host on
        # an older floor is not broken, it just predates the diagnostic. Its
        # ABSENCE on this host would mean the >=2.7.1 floor did not actually
        # reach the image, i.e. the Docker cache trap fired.
        pass
    else:
        try:
            payload["geo"] = {
                "configured": bool(geo.is_configured()),
                "denied": len(
                    geo.effective_policy().get("deny_countries") or []
                ),
                "resolved": _resolved_country(),
            }
        except Exception:  # never let a diagnostic break the health probe
            payload["geo"] = {"configured": False, "denied": 0, "error": True}

    return payload


def register_health_route(app, backend: str) -> None:
    """Mount ``/healthz`` on Flask/Quart. No-op on FastAPI (already typed)."""
    if backend == "fastapi":
        return

    server = app.server

    # Built PER REQUEST, not once at registration. It used to be a snapshot
    # closed over by the route — harmless while every field was static
    # (ok/backend/dash_version/build never change for a running process),
    # and silently wrong the moment one is not: `geo` reports live state and
    # this route is registered long before any geo configuration runs, so a
    # snapshot would report the guardrail as unconfigured on a host where it
    # is configured — the diagnostic lying in exactly the situation it
    # exists for (found on llms-2plot-dev 2026-08-23; this host carried the
    # same snapshot until the round-3 sync).
    if backend == "quart":
        from quart import jsonify

        @server.get("/healthz")
        async def _healthz():  # pragma: no cover — quart runtime
            return jsonify(health_payload(backend))
    else:
        from flask import jsonify

        @server.get("/healthz")
        def _healthz():
            return jsonify(health_payload(backend))

    print(f"[dash-pannellum] /healthz registered ({backend}) — "
          "the 2plot.ai hourly health sweep probes this path.")
