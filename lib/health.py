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

import json
import os
import platform
from pathlib import Path

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


def _resolved_country(headers=None) -> str:
    """``geo.explain_resolution`` over THIS request's headers, or a reason.

    Reads the request headers directly rather than anything the package
    threads through, so it answers "did the country header reach this app
    at all?" independently of how the enforcement seam is wired.

    Each route passes its OWN framework's headers explicitly. The first
    version read Flask's request context, which made the FastAPI and Quart
    lanes answer "no request context" forever — and this host is where that
    showed, because it runs ``DASH_BACKEND=fastapi`` in production: the
    typed route the hub sweeps could never see a Flask context, so the one
    field that says "did the country header reach this app at all?" gave
    the same non-answer on every sweep (found hours after the >=2.7.1 floor
    round shipped; template 1.6.12). ``normalize_headers`` accepts
    Flask/Starlette/Quart/dict and never raises. The Flask-context fallback
    stays for callers that pass nothing.
    """
    try:
        from dash_improve_my_llms import geo
        from dash_improve_my_llms._headers import normalize_headers
    except Exception:
        return "unavailable (pre-2.7.0 package)"

    try:
        if headers is not None:
            return geo.explain_resolution(normalize_headers(headers))

        from flask import has_request_context, request

        if not has_request_context():
            return "no request context"
        return geo.explain_resolution(normalize_headers(request.headers))
    except Exception:
        return "unavailable"


def _llms_version() -> dict:
    """``{"llms_version": "2.9.4"}``, or ``{}`` if the package cannot be read.

    Omitted rather than reported as "unknown": a health payload that invents
    a version is worse than one that is silent about it, and run.py's boot
    floor already refuses to start below the floor — so an absent key here
    means the import broke after boot, which is itself the finding.

    THIS FIELD IS WHY THIS HOST NEEDS IT MOST (1.6.44 item 1). Production
    here runs ``DASH_BACKEND=fastapi`` behind a Docker layer cache, and no
    session has ever been able to measure which dash-improve-my-llms wheel
    the running image actually carries: a local image build resolved 2.9.2
    only via a cache HIT, and nothing on the wire named a version. Every
    statement about this host's package version has been inferred from
    requirements.txt, which a `>=` line does not determine. This key ends
    that by reporting the resolved version from inside the process.
    """
    try:
        import dash_improve_my_llms as _pkg

        version = getattr(_pkg, "__version__", None)
        return {"llms_version": version} if version else {}
    except Exception:
        return {}


def _geo_headers_seen() -> list:
    """The visitor-location headers the tracker has seen this process.

    Read through the tracker rather than re-read here: one module decides
    what counts as a location header, and a health probe that kept its own
    list would drift from the one doing the recording.
    """
    try:
        from lib.analytics_tracker import geo_headers_seen

        return geo_headers_seen()
    except Exception:
        return []


def _ledger_block() -> dict:
    """``{"path", "persistent", "visits", "reads"}`` — the ledger, from outside.

    1.6.44 item 20. Three facts that were previously invisible on the wire,
    and on THIS host the second one has been an open question in the project
    memory for weeks: render.yaml declares
    ``TRAFFIC_ANALYTICS_FILE=/var/data/visitor_analytics.json`` with a disk,
    but Blueprint env applies only on a sync and ``/healthz`` exposed no
    ledger path, so the only acceptance available was the ABSENCE of a
    ``[visibility] WARNING`` line in a deploy log only the owner can read.

    ``persistent`` is MEASURED, never declared. It is true iff the resolved
    path lies OUTSIDE the repository root — i.e. on a mounted disk such as
    ``/var/data/...``. A path under the app tree is the container filesystem
    and reads false EVEN WHERE A BLUEPRINT DECLARES A DISK: leaflet ran for
    weeks with a declared disk and no disk, and nothing on the wire could
    contradict the declaration. A boolean that reports the deployment's
    intention is worth nothing; this one reports the filesystem.

    ``visits`` and ``reads`` are the two tables' current row counts, read
    from the same file the tracker writes. A missing file is ``0`` and
    ``0`` — never an error, and /healthz stays 200: this block is a
    diagnostic, and a diagnostic that can take the health probe down with it
    is a liability.

    Row CONTENTS never appear here. Counts, a boolean and a path.
    """
    block = {"path": None, "persistent": False, "visits": 0, "reads": 0}
    try:
        from lib.analytics_tracker import analytics_path

        path = Path(analytics_path()).resolve()
        block["path"] = str(path)
        repo_root = Path(__file__).resolve().parent.parent
        try:
            path.relative_to(repo_root)
            block["persistent"] = False      # inside the tree: container fs
        except ValueError:
            block["persistent"] = True       # outside it: a mounted disk

        if path.exists():
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                for table in ("visits", "reads"):
                    rows = data.get(table)
                    block[table] = len(rows) if isinstance(rows, list) else 0
    except Exception:
        # Never let a diagnostic break the health probe. An unreadable or
        # half-written ledger reports zeros, and the `path` already in the
        # block is what a reader needs in order to go and look.
        pass
    return block


def health_payload(backend: str, headers=None) -> dict:
    payload = {
        "ok": True,
        "backend": backend,
        "dash_version": dash.__version__,
        # The RESOLVED dash-improve-my-llms version (1.6.44 item 1's rider;
        # excalidraw's name and shape, adopted verbatim so the fleet never
        # carries two spellings of the same key). Additive: the existing
        # keys stay and a RENAME is still the failure.
        **_llms_version(),
        # WHICH interpreter is actually serving. Before this field the fleet
        # declared several different Pythons per repo (image, CI matrix,
        # render.yaml) and nothing on the wire could contradict any of them —
        # the drift was invisible to the battery by construction (ops-seat
        # finding, 2026-08-25). scripts/network_smoke.py asserts this minor
        # against the Dockerfile's FROM tag, so image and declaration can no
        # longer part ways silently. On THIS host the field also has to reach
        # `HealthResponse` in lib/asgi_routes.py or production (fastapi) drops
        # it — a payload key added here alone is served on Flask and silently
        # ABSENT on the lane the hub actually sweeps.
        "python": platform.python_version(),
        # Where this host's ledger actually lives, whether it survives a
        # deploy, and how much is in it (1.6.44 item 20). Additive.
        "ledger": _ledger_block(),
    }

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
                "resolved": _resolved_country(headers),
                # WHICH visitor-location headers this process has actually
                # received (1.6.44 item 16). Additive and list-shaped on
                # purpose: the Cloudflare "Add visitor location headers"
                # transform is an owner click PER ZONE, so the only honest
                # answer to "is it on for this host?" is the set of headers
                # that have turned up — and it grows as they do, rather than
                # being declared once and going stale. Empty on a host that
                # has served no request carrying one yet.
                "headers_seen": _geo_headers_seen(),
            }
        except Exception:  # never let a diagnostic break the health probe
            payload["geo"] = {"configured": False, "denied": 0,
                              "headers_seen": _geo_headers_seen(),
                              "error": True}

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
    # Each branch hands its OWN framework's headers to the payload: geo's
    # `resolved` reads the country header from THIS request, and the
    # Flask-context fallback inside health_payload can only ever see a
    # Flask one.
    if backend == "quart":
        from quart import jsonify, request

        @server.get("/healthz")
        async def _healthz():  # pragma: no cover — quart runtime
            return jsonify(health_payload(backend, headers=request.headers))
    else:
        from flask import jsonify, request

        @server.get("/healthz")
        def _healthz():
            return jsonify(health_payload(backend, headers=request.headers))

    print(f"[dash-pannellum] /healthz registered ({backend}) — "
          "the 2plot.ai hourly health sweep probes this path.")
