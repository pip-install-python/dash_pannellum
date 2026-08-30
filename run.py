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

# This satellite's directory key, pinned before ANY module that resolves an
# identity to the hub is imported.
#
# lib/satellite_reporter.py is a byte-copy of the boilerplate's (its shasum
# against the template is a gate-wave acceptance check), and the template's
# copy necessarily defaults to the template's own key, "boilerplate". The
# other three hub-facing modules — lib/ad_client.py, lib/hub_client.py and
# lib/bulletin.py — default to "pannellum". So with SATELLITE_APP_KEY unset
# the four DISAGREE, and the reporter would file this host's traffic under
# the template's row. render.yaml sets the variable in production; this line
# is what makes the guarantee hold without it, and it is a `setdefault`, so
# a deploy that sets the variable still wins.
os.environ.setdefault("SATELLITE_APP_KEY", "pannellum")

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
    on_document_read,
    register_page_metadata,
)

# The version requirements.txt pins. Checked at startup — see the floors block
# below for why this is worth a line of output on every boot.
#
# 2.5.1 was the Tier-B SEO standard: `configure_seo` (icons, social card,
# publisher/sameAs), the crawler <title> carrying the site name, per-page
# `title`/`image_url`/`schema_type` actually reaching the crawler document,
# /favicon.ico answered with a redirect instead of the app shell, and a
# prerender that no longer clobbers the browser's per-page <title>.
# 2.6.0 raises it to the honesty standard: sitemap <lastmod> is emitted
# verbatim from `register_page_metadata(lastmod=)` and OMITTED when unset.
# The floor is load-bearing for HONESTY, not crash avoidance: older
# packages take `lastmod=` into **kwargs and silently ignore it, so below
# the floor every date this repo stamped is swallowed and the sitemap goes
# back to swearing everything changed at build time. Also in 2.6.0: icon
# autodiscovery (this app still declares explicitly; the two must agree —
# tests/test_seo_icons.py), JSON-LD publisher.logo, and the viewer banner
# de-dup.
# `configure_seo` is deliberately imported AFTER this floor fires (see the
# floors block) so a stale environment gets the floor's diagnosis instead of
# a bare ImportError.
# 2.6.1 additionally serves that prerender VISIBLE — below it the block
# carries a literal `hidden` attribute and every visibility-respecting
# non-JS reader gets "Loading..." instead of the page's prose.
# 2.7.1 is the round-3 fleet floor: 2.7.0 dedups the prerender H1 (the
# injected header's h1 against the doc body's own) and the home footer's
# doubled /llms.txt link, and hardens the idempotency probe so a page
# that merely MENTIONS the prerender marker keeps its prerender. 2.7.1
# adds the llms.txt v2 discovery relations + Link headers, the
# Accept: text/plain ramp, and the representation content digest.
# 2.8.0 is the ledger floor (2026-08-29): ONE classifier — `classify()` is
# the registry robots.txt is rendered from, and lib/analytics_tracker
# delegates to it instead of carrying a fourth UA list that filed ClaudeBot
# (Anthropic's TRAINING crawler) under "search"; the READ EVENT —
# `on_document_read` hands the app one row per corpus document served
# (tier, verdict, bytes, verified vendor), which the tracker keeps as the
# ledger's `reads` table; `Vary: User-Agent` on the lane-split responses;
# and verified vendor identity (`verified` is `n/a` where the operator
# publishes no ranges — Anthropic does not, so ClaudeBot is always n/a).
# 2.8.1 will write the resolved `policy` on every event; until then it is
# None and the rollup groups it as "default". Nothing here waits on it.
LLMS_PKG_FLOOR = (2, 8, 0)

# Analytics tracking
from lib.analytics_tracker import tracker  # noqa: E402

# Site identity, public origin, and the cross-host network directory
from lib.constants import (  # noqa: E402
    APP_TITLE,
    BASE_URL,
    OG_IMAGE_ALT,
    OG_IMAGE_HEIGHT,
    OG_IMAGE_URL,
    OG_IMAGE_WIDTH,
    PUBLISHER,
    SAME_AS,
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
        "Below 2.8.0 there is no `classify()` and no `on_document_read`: the "
        "tracker cannot delegate bot classification and no read row is ever "
        "kept, so the ledger's `reads` table and rollup v4's vendors[] are "
        "empty (ImportError at boot, not a silent degrade). "
        "Below 2.7.1 the llms.txt v2 discovery relations, the Link headers "
        "and the representation digest are absent; below 2.7.0 every page "
        "serves a DUPLICATE H1 to crawlers (the injected header's against "
        "the doc body's own) and a page mentioning the prerender marker "
        "silently loses its prerender. Below 2.6.1 the prerender ships "
        "`hidden` and no-JS readers get \"Loading...\"; below 2.3.4 this "
        "site's published identity degrades to whatever `app.title` is.",
        fatal=True,
    )

# Imported after the floor on purpose: on a pre-2.5.0 package this name does
# not exist, and the floor's diagnosis above beats a bare ImportError. The
# fallback exists only for ALLOW_STALE_DEPS=1 — the floor is fatal otherwise.
try:
    from dash_improve_my_llms import configure_seo  # noqa: E402
except ImportError:  # pragma: no cover — ALLOW_STALE_DEPS with a pre-2.5.0 package

    def configure_seo(**_kwargs) -> None:
        print(
            "[dash-pannellum] WARNING: configure_seo unavailable (pre-2.5.0 "
            "package) — crawler identity tags and root icons not emitted."
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

# Crawler posture — THE WALL IS RETIRED (sync item 15, Round 3.4, owner
# decision 2026-08-29). Until now this host blocked the AI-training crawlers
# (GPTBot, ClaudeBot, CCBot, …): robots.txt said Disallow and the package's
# middleware answered 403 on the browser document and /healthz, while the
# corpus (/llms.txt and the tiers) was open — a wall that decided by vendor
# class what nobody could account for. Measured on this host 2026-08-30,
# before the flip: ClaudeBot and GPTBot both got 403 / 200 / 403 on
# `/`, `/llms.txt`, `/healthz`. The ledger changed the calculus: since
# item 12 every corpus read is a row (tier, vendor, verified, bytes) and the
# hub reconciles it against the wire. A read that is recorded and priceable
# does not need a wall; it needs a policy. So training crawlers are ALLOWED
# by default, the same as search fetchers and traditional bots, and the
# per-vendor knob is the tool from here on — block or meter ONE vendor by
# name when its ledger rows justify it, never the whole class:
#
#     vendor_policy={"bytespider": "block", "gptbot": "meter"}
#
# (2.3.3's per-vendor buckets still matter: they are what makes a per-vendor
# line mean the vendor it names.) ClaudeBot is Anthropic's *training*
# crawler; Claude-User / Claude-SearchBot are the user-triggered and search
# fetchers, allowed all along alongside ChatGPT-User / OAI-SearchBot /
# PerplexityBot.
app._robots_config = RobotsConfig(
    block_ai_training=False,      # training crawlers allowed; the ledger records every read
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
    # The home page of a component library is a SoftwareApplication, not a
    # generic WebPage — the one structured-data type that exactly describes
    # it. Docs pages default to TechArticle in pages/markdown.py.
    schema_type="SoftwareApplication",
)

# ============================================================================
# Site identity for the CRAWLER document (dash-improve-my-llms 2.5.0).
# Until 2.5.0 the generated crawler HTML carried the page's content signals
# and none of its identity: browsers got 4-7 icon links, og:image and a
# twitter card from templates/index.html while Googlebot got zero of any of
# them, on every host in the network — so search showed the generic globe.
# One declaration covers every crawler surface, and it also claims
# /favicon.ico (Google's fallback), which Dash's page catch-all was
# answering with the app shell. Content may differ between the crawler
# document and the browser document; identity may not.
# ============================================================================
configure_seo(
    icons=[
        # Same paths templates/index.html links, so the two heads agree.
        # The .ico href is the assets/favicon/ copy (byte-identical to the
        # root one index.html links) so this list is SET-equal to what
        # 2.6.0's autodiscovery finds — tests/test_seo_icons.py pins that
        # agreement, which is the proof the fleet can rely on discovery
        # alone once its pixels are right.
        "/assets/favicon/favicon.ico",
        {"href": "/assets/favicon/favicon-32x32.png", "sizes": "32x32"},
        {"href": "/assets/favicon/favicon-16x16.png", "sizes": "16x16"},
        {"href": "/assets/favicon/favicon-96x96.png", "sizes": "96x96"},
        {"href": "/assets/favicon/android-chrome-192x192.png", "sizes": "192x192"},
        {"href": "/assets/favicon/android-chrome-512x512.png", "sizes": "512x512"},
        {"href": "/assets/favicon/apple-touch-icon.png",
         "rel": "apple-touch-icon", "sizes": "180x180"},
    ],
    social_image=OG_IMAGE_URL,
    social_image_alt=OG_IMAGE_ALT,
    social_image_width=OG_IMAGE_WIDTH,
    social_image_height=OG_IMAGE_HEIGHT,
    publisher=PUBLISHER,
    same_as=SAME_AS,
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
from lib import page_tiers as _page_tiers  # noqa: E402
from lib import page_visibility as _page_visibility  # noqa: E402

# Tiered corpus documents (dash-improve-my-llms >= 2.4.0). Pseudo-paths:
# they never enter dash.page_registry, so they cannot leak into listings —
# registering them here lets this satellite tier its compact briefing and
# full corpus via env (LLMS_SMALL_TIER / LLMS_FULL_TIER), and the hub can
# tighten either network-wide through its page-tier ceilings with no
# redeploy here. The explicit `or "public"` matters: these registered under
# the PAGE_DEFAULT_TIER fallback before, which meant flipping that env to
# gate the *interactive* site would silently gate the corpus documents too.
# Their tier is now always a deliberate setting, never an ambient default.
_page_tiers.register("/llms-small.txt",
                     os.environ.get("LLMS_SMALL_TIER") or "public")
_page_tiers.register("/llms-full.txt",
                     os.environ.get("LLMS_FULL_TIER") or "public")

# The home page registers via pages/home.py, not pages/markdown.py, so no
# frontmatter ever declares its tier — under PAGE_DEFAULT_TIER=auth it would
# silently inherit the gate. The funnel's front door stays public, always.
_page_tiers.register("/", "public")

# force= when either gate env is present: with every tier still public the
# auto-detect would skip the wiring, but a host that flips by env needs the
# verdict plumbing (and the prerender's use of it) live during the dark
# launch, not on the flip.
ACCESS_ENABLED = _access.configure(
    force=bool(os.environ.get("PAGE_DEFAULT_TIER")
               or os.environ.get("LLMS_PUBLIC_DEFAULT"))
)

# Wire up the package: /llms.txt, /<page>/llms.txt, /robots.txt, /sitemap.xml,
# bot-detection middleware, and (on Dash 4.3+) MCP resource registration.
# Works under Flask, FastAPI, and Quart — no gating needed.
add_llms_routes(app, LLMSConfig(warn_missing_llms_doc=True))

# The ledger row (sync item 12, dimll 2.8.0): the package emits one event per
# corpus document it serves and does no I/O with it; the tracker keeps it
# as the `reads` table next to `visits`. Registered ONCE — the test suite
# imports run.py more than once per process and `on_document_read`
# appends, so a marker on the callback's owner guards the second import
# (the package also dedups an identical callable; belt and braces).
if not getattr(tracker, "_read_hook_registered", False):
    on_document_read(tracker.record_read)
    tracker._read_hook_registered = True

# ============================================================================

app.layout = create_appshell(dash.page_registry.values())

server = app.server

# ============================================================================
# The person→agent handoff: /api/agent-key turns the browser's Clerk session
# into a portable ?key= for copied llms.txt URLs (lib/agent_key.py). 204 for
# everyone until Clerk and the hub are configured — safe to mount always.
# ============================================================================

from lib.agent_key import register_agent_key_route  # noqa: E402

register_agent_key_route(app, BACKEND)

# The gate's boot line. Prefixed `[boilerplate/<app>]` rather than this
# repo's usual `[dash-pannellum]` on purpose: the gate-wave acceptance is
# read from the deploy log across all 14 hosts, and one uniform prefix is
# what makes that grep work fleet-wide.
_non_public = sum(1 for t in _page_tiers.registered().values() if t != "public")
print(
    f"[boilerplate/pannellum] interactive gate: default tier "
    f"'{os.environ.get('PAGE_DEFAULT_TIER') or 'public'}', "
    f"{_non_public} non-public page(s), machine surfaces "
    f"{'GATED' if not _page_tiers.get_llms_public('/__probe__') else 'open'} "
    f"by default (LLMS_PUBLIC_DEFAULT), access wiring "
    f"{'ON' if ACCESS_ENABLED else 'off'}, control board at "
    f"/admin/control-board ({_page_visibility.override_count()} live "
    f"override(s))."
)

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
