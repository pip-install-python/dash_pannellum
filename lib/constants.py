import os

# ---------------------------------------------------------------------------
# Site identity — one string, every surface
# ---------------------------------------------------------------------------
# The network standard (2plot.ai, 2plot.dev, boilerplate.2plot.dev,
# leaflet.2plot.dev and email.2plot.dev all ship it): a site states what it
# is, in the same words, on every surface an agent or a reader can reach.
# The surfaces this brand has to reach, and what serves each:
#
#   Dash(title=SITE_BRAND)              -> <title>, and the fallback identity
#   register_page_metadata(path="/",    -> the /llms.txt H1 and the llms
#       name=SITE_BRAND)                   viewer's brand chip, both via
#                                          dash-improve-my-llms 2.3.4's
#                                          `resolve_site_title`
#   pages/home.md's opening `# ` line   -> the home page's own prose
#
# tests/test_site_identity.py pins all of them to this constant, because the
# failure is silent: `resolve_site_title` SKIPS generic candidates ("Home",
# "Index", Dash's default "Dash") rather than publishing them, so a site that
# never states its identity falls through to whatever is left and nothing
# looks broken.
#
# Naming rules, from the network standard:
#   - "Pip Install Python" is the byline (who made it), never the site name;
#   - the package name LEADS, because for a component library the package IS
#     what a reader came to find. Same shape as leaflet.2plot.dev
#     ("dash-leaflet2 — Leaflet 2 maps for Dash") and email.2plot.dev
#     ("dash-email — email components for Dash"). The boilerplate keeps its
#     package name out of its brand for the opposite reason: nobody installs
#     a template.
SITE_BRAND = "dash-pannellum — 360° panoramas for Dash"

SITE_DESCRIPTION = (
    "dash-pannellum — interactive 360° panoramas, virtual tours, "
    "multi-resolution tiles and 360° video for Plotly Dash, built on the "
    "plug-in-free Pannellum WebGL viewer. Equirectangular and tiled "
    "panoramas, guided tours with scene-switch and callback hotspots, and "
    "live pitch/yaw/scene readouts in Dash callbacks. By Pip Install Python."
)

# Resolves {%title%} in templates/index.html, which is what the served HTML
# carries when dash-improve-my-llms is not rewriting the title per page.
# Per-page titles still come from PAGE_TITLE_PREFIX below.
APP_TITLE = SITE_BRAND

# The brand without its tagline. SITE_BRAND is right for a page that has room
# for it; this is for the places that prefix something else and would
# otherwise run past every platform's truncation point.
SITE_SHORT_NAME = "dash-pannellum"

# The top bar's wordmark. It is SITE_SHORT_NAME and not "Dash Pannellum":
# the 2.0.0 identity pass made the PACKAGE NAME the brand on every surface
# ("a name that matches no installable package" is what it retired), and
# the header was the one surface it missed. Fixed with sync item 16.
WORDMARK = SITE_SHORT_NAME

# The header's identity, out of components/header.py (sync item 18's
# LOGO_ASSET seam, ported into this tree's shape). The template names an
# IMAGE file (`LOGO_ASSET = "ddb.png"`); this site's mark is an Iconify
# glyph, so the constant is the icon name and there is no asset to ship.
# The contract is the same and it is the point of the seam: the header
# holds no identity of its own, a fork changes these four lines.
LOGO_ICON = "mdi:panorama-sphere-outline"
LOGO_WIDTH = 34
WORDMARK_COLOR = "#12B886"
# `sm`, not the template's `xs`: this header's row carries one control more
# than the template's, and the wordmark is what pushes it past a phone's
# edge. visibleFrom REMOVES the node from the accessibility tree, which is
# why the home link carries its own aria-label (item 16, muicharts' note).
WORDMARK_VISIBLE_FROM = "sm"

# Prefixed to every per-page title (`pages/markdown.py`, `pages/home.py`), and
# therefore NOT only a browser-tab string: Dash passes the page title straight
# into `og:title` and `twitter:title` (dash/_pages.py `_page_meta_tags`), so
# this is the headline on every share card the site produces.
#
# Derived rather than retyped so the two cannot drift apart;
# tests/test_site_identity.py pins the relationship. It read "Dash Pannellum | "
# until the network pass — a name that matches no package on PyPI, so every
# unfurl advertised a thing that could not be looked up.
PAGE_TITLE_PREFIX = f"{SITE_SHORT_NAME} | "

PRIMARY_COLOR = "teal"

# Keep in step with pyproject.toml and package.json when cutting a release.
APP_VERSION = "0.4.1"

# ONE constant for the repository. The header's GitHub icon, the Resources
# block and JSON-LD `sameAs` all read it (sync item 16): a fork sets it once.
# NOTE the UNDERSCORE — github.com/pip-install-python/dash_pannellum is the
# real repo (it is what `git remote` says and what SAME_AS has always used).
# The hyphenated spelling that stood here, and in the header's icon href,
# 404s; measured 2026-08-30. The PyPI project is `dash-pannellum` with a
# hyphen, which is where the confusion came from — the two genuinely differ.
GITHUB_URL = "https://github.com/pip-install-python/dash_pannellum"

# ---------------------------------------------------------------------------
# The network's internal-traffic contract
# ---------------------------------------------------------------------------
# The analytics point of truth is https://2plot.ai/docs/satellite-analytics
# ("Internal traffic"): any request whose User-Agent contains
# INTERNAL_UA_TOKEN is 2plot network machinery talking to itself — the hub's
# hourly health sweep, CI smoke batteries, the 4x-daily heartbeat, this app's
# own server-to-server calls to the hub. It is counted NOWHERE.
#
# Two halves, and both are required for the contract to hold:
#
#   inbound  — every tracker drops a token-carrying request at WRITE time,
#              before device detection and before bot classification, so it
#              never reaches the ledger the hourly rollup is built from;
#   outbound — every call this host makes to another network host sends
#              INTERNAL_UA, so the far side can apply the same rule.
#
# The token string must stay byte-identical across the network; it mirrors
# 2plotai/lib/constants.py, pip-docs+/lib/constants.py, the boilerplate's,
# leaflet's and dash-email's.
INTERNAL_UA_TOKEN = "2plot-internal"
INTERNAL_UA = "2plot-internal/1.0 (+https://2plot.ai/docs/satellite-analytics)"


def internal_ua(caller: str = "") -> str:
    """``INTERNAL_UA`` with a caller suffix, e.g. ``"ad-client"``.

    The suffix is for reading logs on the far side; only the token matters to
    the contract, and it stays intact whatever the suffix says.
    """
    caller = (caller or "").strip()
    return f"{INTERNAL_UA} {caller}" if caller else INTERNAL_UA


# ---------------------------------------------------------------------------
# Public origin
# ---------------------------------------------------------------------------
# The single source of truth for every absolute URL this app emits:
# <link rel="canonical">, sitemap.xml, robots.txt and the llms.txt links.
#
# Leaving APP_BASE_URL unset in production is correct: unlike the boilerplate
# (whose default is the TEMPLATE's origin, so inheriting it deindexes a fork),
# the default here is this app's own canonical public origin. What is still
# caught by require_owned_base_url() below is the failure that actually bites
# — a platform-generated hostname. `*.onrender.com` keeps resolving after a
# custom domain is attached, so canonicals pointing there split link equity
# across two hosts for as long as nobody notices.
DEFAULT_BASE_URL = "https://pannellum.2plot.dev"
BASE_URL = os.environ.get("APP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

# ---------------------------------------------------------------------------
# The social card
# ---------------------------------------------------------------------------
# Dash builds `og:image` and `twitter:image` for every page from
# `register_page(image_url=...)`, and emits `content=""` when it finds neither
# an explicit URL nor an inferable asset (dash/_pages.py). An EMPTY og:image
# unfurls WORSE than having no tag at all, because scrapers treat the empty
# value as the declared image and render a blank card.
#
# THE CARD LIVES ON THE CDN, NOT IN assets/. Network rule, about cold starts
# rather than tidiness: a card served by the app is fetched by the scraper at
# unfurl time, and on a cold free-tier container that request lands mid-wake
# and times out. The preview renders blank ONCE and the platform caches the
# miss — so the first person to share the link poisons it for everyone.
#
# Rendered by `scripts/make_social_card.py` (1200x630 = 1.91:1, the Open
# Graph ideal) and uploaded BY HAND to the Cloudflare bucket. There is no
# automated path to that bucket, and og:image must not point at the CDN URL
# until the object is verified there (200 + IHDR 1200x630, read as BYTES).
#
# The width and height MUST match the file. tests/test_social_card.py pins
# these against templates/index.html, and scripts/smoke_live.py fetches the
# real CDN object after every deploy and reads its IHDR chunk.
OG_IMAGE_URL = "https://cdn.2plot.ai/github_assets/pannellum.2plot.dev.png"
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630
OG_IMAGE_TYPE = "image/png"
OG_IMAGE_ALT = SITE_BRAND

# The package cross-link block — who publishes this site, and which other
# URLs are the same entity. `SAME_AS` becomes JSON-LD `sameAs` on every
# crawler page: for a docs satellite it should list the documented package's
# GitHub repo and PyPI project — three properties pointing at each other is
# the strongest statement of which URL is a package's canonical docs home.
# A fork sets these once; the other half of the loop (PyPI project_urls and
# the GitHub README pointing back at the docs subdomain) is a per-package
# checklist item, not code. dash-pannellum ships on PyPI, so the PyPI
# project joins the repo here — the boilerplate lists only a repo because
# nobody pip-installs a template.
PUBLISHER = "Pip Install Python LLC"
PYPI_URL = "https://pypi.org/project/dash-pannellum/"
# DIVERGENCE from the template's `SAME_AS = [GITHUB_URL]`: this repo IS a
# published package, so the PyPI project joins the repo here. The item's
# contract — GITHUB_URL is the single source for the repository — is kept;
# the list is one entry longer. The boilerplate names only a repo because
# nobody pip-installs a template.
SAME_AS = [GITHUB_URL, PYPI_URL]

# ---------------------------------------------------------------------------
# Navigation contract (sync item 16) — the parts of the sidebar/top bar that
# are IDENTICAL on every host come from template code and these constants;
# the app's own sections come from frontmatter. A fork edits THIS block and
# its docs' frontmatter, never components/navbar.py.
# ---------------------------------------------------------------------------

# The app's own sections, in sidebar order. Every docs page declares
# `category:` in its frontmatter; categories not listed here follow the
# listed ones, alphabetically. Keep names short — they are sidebar titles.
CATEGORY_ORDER = [
    "Getting started",
    "Panoramas",
    "Interaction",
]

# Network-wide community links — identical on every host.
DISCORD_URL = "https://discord.gg/e5s5uHWUHH"
YOUTUBE_URL = "https://www.youtube.com/@2plotai"
YOUTUBE_SUBSCRIBE_URL = YOUTUBE_URL + "?sub_confirmation=1"
DMC_URL = "https://www.dash-mantine-components.com/"

# The upstream project this component wraps. dash-pannellum is a Dash
# wrapper around Pannellum, the plug-in-free WebGL panorama viewer — the
# thing a reader of these docs most often needs next.
UPSTREAM = {"name": "Pannellum", "url": "https://pannellum.org/",
            "icon": "mdi:panorama-sphere"}

# Dash component packages whose props the generated /api page documents.
# The version badge in the header reads the first entry's __version__.
API_PACKAGES: list = ["dash_pannellum"]

# The owner's profile — the FOOTER's GitHub link (the repo is the top bar's).
GITHUB_PROFILE_URL = "https://github.com/pip-install-python"


def resources() -> list:
    """The sidebar's Resources section: THIRD-PARTY ONLY (owner, 2026-08-30).
    `dmc` and, when a fork declares it, the upstream project. The owner's
    own links (repo, Discord, YouTube) live in the top bar and the footer,
    never here; no community.plotly.com; no pip-install-python.com."""
    items = [
        {"label": "dmc", "url": DMC_URL, "icon": "ic:baseline-design-services"},
    ]
    if UPSTREAM:
        items.append({"label": UPSTREAM["name"], "url": UPSTREAM["url"],
                      "icon": UPSTREAM.get("icon", "mdi:open-in-new")})
    return items


def require_owned_base_url(base_url: str = BASE_URL) -> None:
    """Fail fast in production when BASE_URL isn't this app's real origin.

    Only enforced when a hosting platform is detected (Render sets ``RENDER``;
    ``APP_ENV=production`` works anywhere else), so local development and the
    test suite are unaffected.

    Unlike the boilerplate's copy this does NOT require APP_BASE_URL to be
    set: ``DEFAULT_BASE_URL`` here is this app's own origin rather than a
    template's, so inheriting it is correct. What is still caught is a
    platform-generated hostname — ``*.onrender.com`` keeps resolving after
    the custom domain is attached, and canonicals pointing there split link
    equity across two hosts.
    """
    in_production = bool(
        os.environ.get("RENDER") or os.environ.get("APP_ENV") == "production"
    )
    if not in_production:
        return

    for platform_host in ("onrender.com", "herokuapp.com", "railway.app", "fly.dev"):
        if platform_host in base_url:
            raise RuntimeError(
                f"base URL {base_url!r} is a platform-generated hostname. "
                "Canonical tags, sitemap.xml and llms.txt would all point at "
                "it instead of the custom domain, splitting link equity "
                "across two hosts. Set APP_BASE_URL to the public domain."
            )


# Height of the fixed AppShell header, in px. Consumed by AppShell(header=...)
# and by the mobile drawer, which docks itself directly below the header.
HEADER_HEIGHT = 70

# This will be populated by pages/markdown.py when loading documentation files
NAME_CONTENT_MAP = {}
PROPS_TO_EXCLUDE = [
    "unstyled",
    "m",
    "my",
    "mx",
    "mt",
    "mb",
    "ms",
    "me",
    "ml",
    "mr",
    "p",
    "py",
    "px",
    "pt",
    "pb",
    "ps",
    "pe",
    "pl",
    "pr",
    "bg",
    "c",
    "opacity",
    "ff",
    "fz",
    "fw",
    "lts",
    "ta",
    "lh",
    "fs",
    "tt",
    "td",
    "w",
    "miw",
    "maw",
    "h",
    "mih",
    "mah",
    "bgsz",
    "bgp",
    "bgr",
    "bga",
    "pos",
    "top",
    "left",
    "bottom",
    "right",
    "inset",
    "display",
    "flex",
]
