"""
``/healthz`` liveness probe for the Flask and Quart backends.

The 2plot.ai hub sweeps every satellite's ``/healthz`` once an hour and records
up/down + latency — that's the "Satellite health & reach" panel on ``/traffic``
(the traffic rollup this app POSTs supplies the other half). The FastAPI build
already declares a typed ``/healthz`` in ``lib/asgi_routes`` so it shows up in
Swagger; this module gives the other two backends the same endpoint, so the
probe result doesn't depend on which backend a deployment happens to run.

Keep it cheap: the hub measures the round trip, so any work done here is
reported back as this app being slow.
"""
from __future__ import annotations

import os

import dash

from lib.satellite_reporter import app_key


def reporting_enabled() -> bool:
    """Whether the rollup can actually POST (the HMAC secret is set).

    lib/satellite_reporter.py is a BYTE-COPY of the boilerplate's (its
    shasum against the template is a gate-wave acceptance check), and the
    gate-wave template dropped this helper — the boilerplate's own /healthz
    doesn't publish a `reporting` field, so upstream had no use for it.
    This host does publish it, so the predicate lives here instead of
    reaching into the reporter's private `_secret()`: importing a private
    name across a module we are contractually required to re-copy verbatim
    would break silently on the next sync. One env read, same semantics.
    """
    return bool(os.getenv("CROSS_APP_WEBHOOK_SECRET"))


def health_payload(backend: str) -> dict:
    # `app` is the RESOLVED reporting key, not a constant: a mis-set
    # SATELLITE_APP_KEY overwrites another app's analytics rows on the hub,
    # and exposing the effective value here is how the fleet battery catches
    # that (the flows deploy once reported as "email" — found via healthz).
    return {
        "ok": True,
        "app": app_key(),
        "backend": backend,
        "dash_version": dash.__version__,
        "reporting": reporting_enabled(),
    }


def register_health_route(app, backend: str) -> None:
    """Mount ``/healthz`` on Flask/Quart. No-op on FastAPI (already typed)."""
    if backend == "fastapi":
        return

    server = app.server
    payload = health_payload(backend)

    if backend == "quart":
        from quart import jsonify

        @server.get("/healthz")
        async def _healthz():  # pragma: no cover — quart runtime
            return jsonify(payload)
    else:
        from flask import jsonify

        @server.get("/healthz")
        def _healthz():
            return jsonify(payload)

    print(f"[dash-pannellum] /healthz registered ({backend}) — "
          "the 2plot.ai hourly health sweep probes this path.")
