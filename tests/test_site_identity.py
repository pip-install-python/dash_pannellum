"""Site identity: one brand, every surface, verbatim.

The network standard says a site states what it is in the same words
everywhere an agent or a reader can reach. The failure this pins is silent,
which is why it needs tests rather than a code review: nothing errors when a
surface falls back to a default.

What was live before this repo joined the network: every surface read
**"Dash Pannellum"** — not a framework default, but not the network's
identity either. There is no package called "Dash Pannellum" on PyPI; the
brand an agent publishes has to be the string that finds the thing:
`dash-pannellum`.

dash-improve-my-llms 2.3.4's `resolve_site_title` is what makes the fix
possible: it takes the home page's registered `name` first, `app.title`
second, and *skips* generic candidates ("Home", "Index", "Dash") rather than
publishing them. These tests assert both ends of that — the inputs this repo
controls, and the H1 it produces.
"""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from lib.constants import (
    PAGE_TITLE_PREFIX,
    SITE_BRAND,
    SITE_DESCRIPTION,
    SITE_SHORT_NAME,
)

# Spelled out rather than imported, so that renaming the constant cannot
# silently rename the site. Changing the brand should require changing this
# line, deliberately.
EXPECTED_BRAND = "dash-pannellum — 360° panoramas for Dash"

# A markdown-registered docs page whose /llms.txt viewer variant carries the
# network banner. Any registered prose page works; this one is the least
# likely to be renamed.
SAMPLE_PAGE = "/getting-started"


def test_brand_constant_is_the_agreed_identity():
    assert SITE_BRAND == EXPECTED_BRAND


def test_app_title_is_the_brand(app):
    """`Dash(title=...)` — the <title> and `resolve_site_title`'s fallback."""
    assert app.title == EXPECTED_BRAND


def test_home_prose_opens_with_the_brand():
    first = (REPO_ROOT / "pages" / "home.md").read_text().splitlines()[0]
    assert first == f"# {EXPECTED_BRAND}"


def test_llms_index_h1_is_the_brand(client):
    """The single most-read line of this site, and the one nobody looks at."""
    response = client.get("/llms.txt")
    assert response.ok
    assert response.text.splitlines()[0] == f"# {EXPECTED_BRAND}"


def test_llms_index_tagline_is_the_description(client):
    body = client.get("/llms.txt").text
    assert f"> {SITE_DESCRIPTION}" in body


def test_the_viewer_brand_chip_is_not_a_framework_default(client):
    """The chip that reads "Dash" on a pre-2.3.4 artifact.

    It is rendered from the same `resolve_site_title` call as the H1, so
    asserting the brand is present catches both a stale package and a
    regressed constant. The banner is templated markup, so the brand may
    arrive HTML-escaped — compare both spellings rather than failing for a
    reason that has nothing to do with identity.
    """
    import html as html_module

    from conftest import BROWSER_ACCEPT

    page = client.get(f"{SAMPLE_PAGE}/llms.txt", accept=BROWSER_ACCEPT).text
    assert html_module.escape(EXPECTED_BRAND) in page or EXPECTED_BRAND in page, (
        "the viewer banner does not name this site"
    )


def test_the_byline_is_in_the_description_not_the_brand():
    """Naming rules from the standard.

    The brand says what the site *is*; the byline says who made it. A brand of
    "Pip Install Python" would make every satellite in the network share one
    name.

    The PACKAGE name is deliberately allowed in the brand here, unlike the
    documentation boilerplate: for a component library the package IS what a
    reader came to find, which is why leaflet.2plot.dev ships
    "dash-leaflet2 — Leaflet 2 maps for Dash". Nobody installs a template; a
    lot of people install this.
    """
    assert "dash-pannellum" in SITE_DESCRIPTION
    assert "Pip Install Python" in SITE_DESCRIPTION
    assert "Pip Install Python" not in SITE_BRAND


def test_no_surface_falls_back_to_a_generic_title():
    """The values `resolve_site_title` is designed to skip.

    If the brand were ever set to one of these, the package would silently
    fall through to the next candidate and this repo would have no idea which
    string it was publishing.
    """
    from dash_improve_my_llms.handlers import _GENERIC_SITE_TITLES

    assert SITE_BRAND.strip().lower() not in _GENERIC_SITE_TITLES


def test_readme_agrees_with_the_brand():
    """A README that names the site differently is the next drift."""
    readme = (REPO_ROOT / "README.md").read_text()
    assert EXPECTED_BRAND in readme, "README.md does not state the site brand"


def test_llms_package_floor_is_the_network_standard():
    """Identity resolution lives in the package; the floor is what delivers it."""
    import dash_improve_my_llms as pkg

    parts = tuple(int(p) for p in pkg.__version__.split(".")[:3] if p.isdigit())
    assert parts >= (2, 3, 4), (
        f"dash-improve-my-llms {pkg.__version__} predates resolve_site_title; "
        "the viewer chip and the /llms.txt H1 would fall back to app.title"
    )


# ---------------------------------------------------------------------------
# The per-page title — a share-card surface, not just a browser tab
#
# Dash passes each page's `title` straight into `og:title` and `twitter:title`
# (dash/_pages.py `_page_meta_tags`). PAGE_TITLE_PREFIX therefore sets the
# headline of every unfurl this site produces. Nobody sees their own share
# cards, so only a test catches it.
# ---------------------------------------------------------------------------


def test_the_page_title_prefix_is_derived_from_the_short_name():
    assert PAGE_TITLE_PREFIX == f"{SITE_SHORT_NAME} | "


def test_the_short_name_cannot_drift_from_the_brand():
    """Two constants, one identity. Derived, so this should be automatic."""
    assert SITE_BRAND.startswith(SITE_SHORT_NAME)


def test_the_share_card_headline_names_this_site(client):
    """og:title and twitter:title, as a scraper reads them."""
    html = client.get("/").text
    for tag in ("og:title", "twitter:title"):
        found = re.findall(
            rf'<meta[^>]*property="{tag}"[^>]*content="([^"]*)"', html
        )
        assert found, f"no {tag} on the home page"
        for value in found:
            assert SITE_SHORT_NAME in value, f"{tag}={value!r} does not name this site"


def test_no_identity_surface_still_carries_the_old_display_name():
    """A sweep of the files that PUBLISH identity — and only those.

    "Dash Pannellum" was every surface's name before the network pass.
    Comments and docstrings are stripped first: several files document the
    old value while explaining the fix, and that is the one legitimate
    mention. Scope stays narrow (LESSONS §7): the docs prose legitimately
    refers to the viewer by prose names, and the component class itself is
    `DashPannellum`, which is not this site's display name.
    """
    offenders = []
    for path in ("lib/constants.py", "templates/index.html",
                 "scripts/network_smoke.py", "pages/home.md"):
        text = (REPO_ROOT / path).read_text()
        if path.endswith(".py"):
            text = re.sub(r'"""(?:.|\n)*?"""', "", text)
            text = re.sub(r"#.*", "", text)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        if "Dash Pannellum" in text:
            offenders.append(path)
    assert offenders == [], f"the old display name survives in {offenders}"
