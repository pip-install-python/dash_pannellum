"""
dash-pannellum documentation site — 360° panoramas for Dash, markdown-driven.

Serves the component documentation (docs/**/*.md) with live examples.
Deployed at https://pannellum.2plot.dev as a 2plot network satellite.

Run locally:

    python run.py                          # backend from .env (DASH_BACKEND)
    DASH_BACKEND=flask python run.py       # Flask fallback

Production (Render/Docker):

    gunicorn run:server -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8561
"""
import inspect
import os
import sys

from dotenv import load_dotenv

# MUST come before the first-party imports below, and this is not style.
# Several modules read os.environ at *import* time — lib/constants.py
# (APP_BASE_URL), lib/ad_client.py (AD_SERVER_URL, AD_APP_ID) and
# lib/analytics_tracker.py (TRAFFIC_ANALYTICS_FILE). Loading the .env after
# importing them means every one of those silently falls back to its default
# no matter what the file says.
load_dotenv()

import dash  # noqa: E402
from dash import Dash  # noqa: E402
from components.appshell import create_appshell  # noqa: E402


def _version(text: str) -> tuple:
    """("4.4.1rc0") -> (4, 4, 1). Trailing rc/dev segments are dropped."""
    parts = []
    for chunk in text.split(".")[:3]:
        digits = ""
        for char in chunk:
            if not char.isdigit():
                break
            digits += char
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


# Feature gates below are keyed off this rather than off a try/except, so the
# reason a feature is unavailable is stated once, in one place.
DASH_VERSION = _version(dash.__version__)

# AI/LLM Integration & SEO — dash-improve-my-llms >= 2.3.4 from PyPI (the
# vendored 2.0.0 tarball is gone). 2.3.4 brings `resolve_site_title`, which is
# what carries SITE_BRAND into the /llms.txt H1 and the llms viewer's brand
# chip; 2.3.3 fixed the Anthropic bot taxonomy and directive stripping.
from dash_improve_my_llms import (  # noqa: E402
    __version__ as LLMS_PKG_VERSION,
    add_llms_routes,
    LLMSConfig,
    RobotsConfig,
    register_page_metadata,
)

# The version requirements.txt pins. Checked at startup — see the floors block
# below for why this is worth a line of output on every boot.
LLMS_PKG_FLOOR = (2, 3, 4)

# Analytics tracking
from lib.analytics_tracker import tracker  # noqa: E402

# Site identity, public origin, and the cross-host network directory
from lib.constants import (  # noqa: E402
    APP_TITLE,
    BASE_URL,
    SITE_BRAND,
    SITE_DESCRIPTION,
    require_owned_base_url,
)
from lib import network_directory  # noqa: E402

# Backend selection (flask | fastapi | quart) — see lib/backend.py
from lib.backend import resolve_backend, get_backend_info  # noqa: E402

scripts = [
    "https://unpkg.com/hotkeys-js/dist/hotkeys.min.js",
]

# ----------------------------------------------------------------------------
# Pluggable backend (Dash 4.1+)
# ----------------------------------------------------------------------------
BACKEND = resolve_backend()
BACKEND_INFO = get_backend_info(BACKEND)
IS_FLASK = BACKEND == "flask"

print(
    f"[dash-pannellum] Starting Dash {dash.__version__} "
    f"(dash-improve-my-llms {LLMS_PKG_VERSION}) on backend='{BACKEND}'"
)

# ----------------------------------------------------------------------------
# Dependency floors — enforced, not advised.
#
# A version below the floor stops the boot and says what to do. The app is
# never wrong-but-running. Set ALLOW_STALE_DEPS=1 to downgrade these to
# warnings if you are deliberately testing an older release.
# ----------------------------------------------------------------------------

ALLOW_STALE_DEPS = os.environ.get("ALLOW_STALE_DEPS", "0") == "1"


def _dependency_floor(message: str, fatal: bool) -> None:
    """Print, or refuse to start. Either way, name the interpreter.

    `sys.executable` is the fact that settles which environment is actually
    serving, and it is the one nobody thinks to check first.
    """
    detail = (
        f"{message}\n"
        f"    running from: {sys.executable}\n"
        f"    expected:     {os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv/bin/python')}\n"
        "    fix: point your run configuration at this project's own .venv, "
        "or reinstall with `pip install -r requirements.txt`.\n"
        "    (set ALLOW_STALE_DEPS=1 to start anyway)"
    )
    if fatal and not ALLOW_STALE_DEPS:
        raise RuntimeError("\n[dash-pannellum] " + detail)
    print("[dash-pannellum] WARNING: " + detail)


if LLMS_PKG_FLOOR > _version(LLMS_PKG_VERSION):
    _dependency_floor(
        f"dash-improve-my-llms {LLMS_PKG_VERSION} is below the "
        f"{'.'.join(str(n) for n in LLMS_PKG_FLOOR)} floor in requirements.txt. "
        "Below 2.3.0 the rendered llms.txt viewer, wordmark and navigation "
        "block do not exist at all; below 2.3.4 this site's published identity "
        "silently degrades to whatever `app.title` happens to be.",
        fatal=True,
    )

if DASH_VERSION < (4, 4):
    # Fatal only on FastAPI, where it is not a degradation but an outage:
    # 4.3.0's ASGI middleware returns before setting the request context, so
    # the page catch-all raises "No active request in context" and every
    # non-root URL 500s. Fixed upstream in 4.4.0. On Flask and Quart the same
    # Dash release works, so a warning is proportionate there.
    _dependency_floor(
        f"dash {dash.__version__} is below the 4.4.0 floor in requirements.txt."
        + (
            " On the FastAPI backend every non-root URL returns 500 "
            "('No active request in context') — an upstream defect in 4.3.0, "
            "fixed in 4.4.0."
            if BACKEND == "fastapi"
            else ""
        ),
        fatal=BACKEND == "fastapi",
    )

# Dash 4.3+ MCP server: exposes layout, components, pages and (whitelisted)
# callbacks to MCP clients over Streamable HTTP. Off unless DASH_MCP_ENABLED=1,
# because it is a live introspection surface on a public host.
#
# This has to be a constructor argument — Dash starts the server during
# __init__, so there is no supported way to switch it on afterwards.
MCP_ENABLED = os.environ.get("DASH_MCP_ENABLED", "0") == "1"
MCP_PATH = os.environ.get("DASH_MCP_PATH", "_mcp")

# ----------------------------------------------------------------------------
# Clerk satellite auth. MUST run BEFORE Dash(...) — register_clerk_auth
# installs @dash.hooks callbacks that fire during app construction, so calling
# it afterwards silently does nothing. Fully optional: a no-op with no CLERK_*
# keys, which is the default. See lib/auth.py.
# ----------------------------------------------------------------------------
from lib import auth as _auth  # noqa: E402

CLERK_ENABLED = _auth.register()

MCP_KWARGS = {}
if MCP_ENABLED:
    if "enable_mcp" in inspect.signature(Dash.__init__).parameters:
        MCP_KWARGS = {"enable_mcp": True, "mcp_path": MCP_PATH}
    else:
        print(
            f"[dash-pannellum] DASH_MCP_ENABLED=1 ignored: dash "
            f"{dash.__version__} has no MCP server (needs >= 4.3)."
        )

app = Dash(
    __name__,
    backend=BACKEND,
    title=APP_TITLE,
    suppress_callback_exceptions=True,
    use_pages=True,
    external_scripts=scripts,
    update_title=None,
    prevent_initial_callbacks=True,
    index_string=open('templates/index.html').read(),
    **MCP_KWARGS,
)

if MCP_KWARGS:
    print(
        f"[dash-pannellum] Dash MCP server enabled at /{MCP_PATH.lstrip('/')} "
        f"(dash {dash.__version__})."
    )

# dash-clerk-auth splits its setup either side of Dash(...): sessions, the
# /api/auth/* routes and per-request identity are wired here. No-op when off.
_auth.configure_app(app)

# ----------------------------------------------------------------------------
# Trust the proxy's forwarded scheme. Immediately after the server object
# exists and before anything can serve a request.
#
# Dash builds `twitter:url` from `request.url` for every page, and behind
# Cloudflare -> Render the last hop is plain HTTP, so production would
# advertise `http://pannellum.2plot.dev/` to every social scraper while
# `og:url` looked correct. Scrapers do not run JavaScript, so the client-side
# canonical sync in the template cannot reach this. See lib/proxy.py.
# ----------------------------------------------------------------------------
from lib import proxy as _proxy  # noqa: E402

PROXY_FIX_APPLIED = _proxy.apply(app, BACKEND)
print(
    "[dash-pannellum] forwarded-scheme trust: "
    + ("on" if PROXY_FIX_APPLIED else "OFF — request.url will report the "
       "scheme of the last proxy hop, and social cards will advertise it")
)

# Expose backend info so layout components can render a badge without
# re-reading the env var (which could drift between processes/workers).
app._backend_info = BACKEND_INFO

# ============================================================================
# AI/LLM & SEO Configuration
# ============================================================================

# Public origin. Drives <link rel="canonical">, sitemap.xml and the absolute
# URLs in llms.txt — refuses to boot in production if it is a
# platform-generated hostname (see lib/constants.py).
require_owned_base_url()
app._base_url = BASE_URL

# Cross-host directory: <link rel="related"> tags, a "## Network" section in
# /llms.txt, and followed links in the prerendered body, so an agent that
# lands on one satellite can enumerate the rest. The peer list lives in
# lib/network_directory.py — one definition, imported by every satellite.
network_directory.apply(BASE_URL)

# Configure bot management policies — the balanced default: block training
# crawlers, allow AI search citations and traditional search. As of
# dash-improve-my-llms 2.3.3 the buckets are correct per vendor: ClaudeBot
# (Anthropic's *training* crawler) sits in the training block, while the
# user-triggered and search fetchers Claude-User / Claude-SearchBot are
# allowed alongside ChatGPT-User / OAI-SearchBot / PerplexityBot.
app._robots_config = RobotsConfig(
    block_ai_training=True,       # Disallow GPTBot, ClaudeBot, CCBot, etc.
    allow_ai_search=True,         # Allow Claude-User/-SearchBot, ChatGPT-User, ...
    allow_traditional=True,       # Allow Googlebot, Bingbot, etc.
    crawl_delay=10,
    disallowed_paths=[],
)

# ============================================================================
# Register supplemental metadata for the home page.
# Markdown-driven pages register their own LLMS_DOC inside pages/markdown.py
# (the expanded markdown body becomes the literal /llms.txt response).
# ============================================================================

# `name` here is not a nav label — dash-improve-my-llms 2.3.4 resolves it into
# the /llms.txt H1 and the llms viewer's brand chip (`resolve_site_title`,
# home-page name first, `app.title` second, generic values skipped). It is the
# site's published identity, so it is SITE_BRAND and nothing else; the package
# name lives in the description. See lib/constants.py.
register_page_metadata(
    path="/",
    name=SITE_BRAND,
    description=SITE_DESCRIPTION,
)

# ============================================================================
# FastAPI native routes (only when running on FastAPI): /healthz,
# /api/backend, /api/pages with OpenAPI/Swagger UI. Mounted BEFORE
# add_llms_routes so the package's catch-all /<page>/llms.txt matcher doesn't
# shadow these. Flask/Quart get the same /healthz via lib/health.py — the
# 2plot.ai hub's hourly sweep and CD's sustained-health loop both probe it,
# and the battery asserts on its `ok: true` field.
# ============================================================================

if BACKEND == "fastapi":
    from lib.asgi_routes import register_asgi_routes
    register_asgi_routes(app, BACKEND_INFO)
    print(
        "[dash-pannellum] FastAPI routers mounted: /healthz, "
        "/api/backend, /api/pages. Swagger UI at /docs, ReDoc at /redoc."
    )
else:
    from lib.health import register_health_route
    register_health_route(app, BACKEND)

# ============================================================================
# Analytics tracking (Flask / Quart) — MUST be registered BEFORE
# add_llms_routes.
#
# `before_request` hooks run in registration order, and the package's
# `_bot_middleware` short-circuits AI-search crawlers (ClaudeBot, ChatGPT-User,
# PerplexityBot, ...) with its own response. Registered after it, this hook
# never runs for exactly the bot traffic a docs site most wants counted, and
# the `bot_hits` we report to 2plot.ai would be quietly too low.
#
# FastAPI is the mirror image and is wired further down: Starlette runs the
# LAST-added middleware outermost, so ours goes on after add_llms_routes.
# ============================================================================

if IS_FLASK:
    from flask import request as _flask_request

    @app.server.before_request
    def track_visitor():
        """Track visitor analytics before each request."""
        try:
            # Headers are passed so the tracker can read the REAL client IP
            # and country from the proxy/CDN (behind Render or Cloudflare,
            # remote_addr is the proxy — every visitor would look like one).
            tracker.track_visit(
                _flask_request.path,
                _flask_request.headers.get('User-Agent', ''),
                _flask_request.remote_addr,
                headers=dict(_flask_request.headers),
            )
        except Exception:
            pass

elif BACKEND == "quart":
    from quart import request as _quart_request

    @app.server.before_request
    async def track_visitor():
        """Track visitor analytics before each request (Quart)."""
        try:
            tracker.track_visit(
                _quart_request.path,
                _quart_request.headers.get('User-Agent', ''),
                _quart_request.remote_addr,
                headers=dict(_quart_request.headers),
            )
        except Exception:
            pass

# Network bulletin — hub-published tips and announcements rendered in the
# header of the llms.txt view. Opt-in: with NETWORK_BULLETIN_URL unset it
# wires nothing and the viewer still renders on the package's defaults. The
# boot line says which of the two states this process is in — an announcement
# that never appears is not a symptom anyone notices.
from lib import bulletin as _bulletin  # noqa: E402

BULLETIN_ENABLED = _bulletin.configure()
print(
    f"[dash-pannellum] network bulletin: {_bulletin.url()} "
    f"(app='{_bulletin.app_id()}')"
    if BULLETIN_ENABLED else
    "[dash-pannellum] network bulletin: off — set NETWORK_BULLETIN_URL="
    f"{_bulletin.HUB_BULLETIN_URL} to render the hub's announcements"
)

# ============================================================================
# Access control (dash-improve-my-llms 2.3). Reads the tiers the pages just
# declared, so it must run after they are registered and before the routes are
# attached. Stays OFF unless some page declares a non-public tier — the policy
# and the reasoning live in lib/access.py.
# ============================================================================

from lib import access as _access  # noqa: E402

ACCESS_ENABLED = _access.configure()

# Wire up the package: /llms.txt, /<page>/llms.txt, /robots.txt, /sitemap.xml,
# bot-detection middleware, and (on Dash 4.3+) MCP resource registration.
# Works under Flask, FastAPI, and Quart — no gating needed.
add_llms_routes(app, LLMSConfig(warn_missing_llms_doc=True))

# ============================================================================

app.layout = create_appshell(dash.page_registry.values())

server = app.server

# ============================================================================
# Analytics Tracking (FastAPI) — added LAST on purpose.
# Starlette runs the most recently added middleware outermost, so registering
# here (after add_llms_routes) puts the tracker in front of the package's bot
# middleware and every request gets counted. The Flask/Quart hooks are the
# mirror image and live above.
# ============================================================================

if BACKEND == "fastapi":
    from lib.asgi_middleware import register_asgi_middleware

    register_asgi_middleware(app)

# ============================================================================
# Network analytics — hourly signed rollup POSTed to 2plot.ai so the hub's
# owner-only /traffic dashboard can chart this app alongside the network.
# No-op unless CROSS_APP_WEBHOOK_SECRET is set.
# ============================================================================

from lib.satellite_reporter import start_reporter  # noqa: E402

start_reporter()

# ============================================================================


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("DASH_DEBUG", "0") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8561")),
    )
