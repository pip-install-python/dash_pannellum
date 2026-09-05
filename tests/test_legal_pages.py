"""The Legal section — 1.6.44 item 15.

Built AFTER item 16, deliberately: the privacy page states what the tracker
stores, and a page written before the mechanism describes a mechanism the
repo does not have.

The load-bearing test in this module is
`test_every_key_a_real_visit_row_carries_is_described`. It does not read the
page against a list of expected words — it drives the actual tracker, takes
the row that actually lands in the buffer, and requires the page to describe
every key in it. A page bound to a fixture would go stale the moment the
tracker changed; this one goes red.
"""
import pytest

from conftest import REPO_ROOT

MACHINE_UA = "curl/8 2plot-internal/probe"


# --------------------------------------------------------- registration ----


def test_both_pages_are_registered_under_legal(app_module):
    import dash

    entries = {p["path"]: p for p in dash.page_registry.values()}
    for path, name in (("/terms", "Terms"), ("/privacy", "Privacy")):
        assert path in entries, f"{path} is not registered"
        page = entries[path]
        assert page["name"] == name
        # Every register_page must pass BOTH image_url and description — one
        # page missing either makes Dash emit an EMPTY og:image, which
        # scrapers prefer over every correct tag.
        assert page.get("description"), f"{path} has no description"
        assert page.get("image_url"), f"{path} has no image_url"


def test_legal_is_last_among_the_apps_own_categories():
    """The drop says "between Components and Admin". This fork has no
    Components category — its component pages are Panoramas and Interaction —
    and Admin is built separately by the navbar, so last-of-the-app's-own is
    the same position in this repo's vocabulary."""
    from lib.constants import CATEGORY_ORDER

    assert CATEGORY_ORDER[-1] == "Legal", CATEGORY_ORDER
    assert "Admin" not in CATEGORY_ORDER, (
        "Admin is the navbar's, not CATEGORY_ORDER's — the placement claim "
        "in the comment above this list depends on it"
    )


def test_the_footer_links_resolve_in_both_lanes(client):
    """Item 15's acceptance. The footer advertises these from every page."""
    for path in ("/terms", "/privacy"):
        assert client.get(path).status == 200
        assert client.get(path, MACHINE_UA).status == 200


def test_both_pages_are_in_the_root_machine_index(client):
    body = client.get("/llms.txt", MACHINE_UA).text
    for path in ("/terms/llms.txt", "/privacy/llms.txt"):
        assert path in body, f"{path} is absent from the root index"


# ------------------------------------------- one document, not two ---------


@pytest.mark.parametrize("path,doc_name", [("/terms", "TERMS_DOC"),
                                           ("/privacy", "PRIVACY_DOC")])
def test_the_browser_and_the_machine_get_the_same_source(client, path, doc_name):
    """ONE markdown string, rendered for one lane and handed to the other.

    A site whose privacy page says one thing to a reader and another to a
    crawler has two privacy policies, and only one of them was reviewed. This
    repo is where the fleet learned that lesson the other way round — a props
    table present in one lane and absent in the other for a fortnight — so
    the assertion names both lanes rather than picking the one that passes.
    """
    import pages.legal as legal

    source = getattr(legal, doc_name)
    machine = client.get(f"{path}/llms.txt", MACHINE_UA).text
    browser = client.get(path).text

    # A distinctive sentence from the source must reach BOTH lanes. Headings
    # rather than prose: the renderer reflows paragraphs into components.
    for heading in [ln[3:].strip() for ln in source.splitlines()
                    if ln.startswith("## ")]:
        assert heading in machine, f"{heading!r} missing from the machine lane"
        assert heading in browser, f"{heading!r} missing from the browser lane"


def test_the_pages_render_something_rather_than_an_empty_container():
    """React #31: a list nested inside a children list renders the page EMPTY
    with a green suite. tests/test_layout_nesting.py is the general guard;
    this is the local one, because `_render` splats a parser result."""
    import importlib

    terms = importlib.import_module("pages.terms")
    privacy = importlib.import_module("pages.privacy")

    for page in (terms, privacy):
        rendered = str(page.layout())
        assert len(rendered) > 2000, f"{page.__name__} rendered {len(rendered)}b"
        assert "Text(" in rendered or "Title(" in rendered


# ----------------------------- the prose is bound to the code --------------


def test_every_key_a_real_visit_row_carries_is_described(tmp_path, monkeypatch):
    """The item's own requirement, and the only test here that can age well.

    Drives the REAL tracker, takes the row that actually lands in the buffer,
    and requires the privacy page to describe every key in it. If the tracker
    starts storing something new, this goes red rather than the page going
    quietly false.
    """
    import lib.analytics_tracker as mod
    from pages.legal import PRIVACY_DOC

    monkeypatch.setattr(mod, "analytics_path", lambda: tmp_path / "a.json")
    monkeypatch.setenv("ANALYTICS_VISITOR_SALT", "test-salt")
    tracker = mod.AnalyticsTracker()
    tracker._buffer.clear()
    tracker.track_visit(
        "/getting-started",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "203.0.113.9",
        headers={"CF-IPCountry": "GB", "CF-IPCity": "Manchester"},
    )
    assert tracker._buffer, "the tracker recorded nothing — this pin is vacuous"
    row = tracker._buffer[0]

    # What each stored key must be described as, in the page's own words.
    described = {
        "timestamp": "**time**",
        "path": "**path**",
        "device_type": "**device type**",
        "user_agent": "**User-Agent**",
        "visitor_key": "**visitor key**",
        "location": "**location**",
        # Only present under ANALYTICS_KEEP_CLIENT_IP=1, which the page also
        # names — so if it ever appears by default the page still covers it.
        "ip_address": "ANALYTICS_KEEP_CLIENT_IP",
    }
    undescribed = sorted(k for k in row if k not in described)
    assert undescribed == [], (
        f"the tracker stores {undescribed} and the privacy page does not "
        "mention it — the page is now false about this site"
    )
    for key in row:
        assert described[key] in PRIVACY_DOC, (
            f"the page's description of {key} ({described[key]!r}) is gone"
        )


def test_the_page_says_the_ip_is_not_stored_and_the_row_agrees(tmp_path,
                                                               monkeypatch):
    """Both halves of the claim, so the prose cannot outlive the mechanism."""
    import lib.analytics_tracker as mod
    from pages.legal import PRIVACY_DOC

    monkeypatch.setattr(mod, "analytics_path", lambda: tmp_path / "a.json")
    tracker = mod.AnalyticsTracker()
    tracker._buffer.clear()
    tracker.track_visit("/", "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36",
                        "203.0.113.9")
    row = tracker._buffer[0]

    assert "Your IP address" in PRIVACY_DOC
    assert "ip_address" not in row, (
        "the page says the address is not stored and the row has one"
    )


def test_the_page_says_there_is_no_outbound_lookup_and_the_module_agrees():
    """Parsed, not grepped — the page and the module both NAME the removed
    service, so a grep would match the documentation of the absence."""
    import ast

    from pages.legal import PRIVACY_DOC

    assert "removed —" in PRIVACY_DOC and "not disabled" in PRIVACY_DOC

    tree = ast.parse((REPO_ROOT / "lib" / "analytics_tracker.py").read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported, "the AST read swept nothing"
    assert not imported & {"requests", "urllib", "httpx", "aiohttp", "socket"}


def test_the_page_points_at_a_field_that_actually_exists():
    """It tells the reader to check `geo.headers_seen` on /healthz. A privacy
    page citing a field nobody has is worse than one citing nothing."""
    from lib.health import health_payload
    from pages.legal import PRIVACY_DOC

    assert "geo.headers_seen" in PRIVACY_DOC
    block = health_payload("flask").get("geo")
    if block is None:
        pytest.skip("no geo block on this package version")
    assert "headers_seen" in block


def test_terms_says_this_repo_is_a_package_as_well_as_a_site():
    """This fork's divergence from the template's Terms, and it is the point.

    A reader arriving at /terms is at least as likely to be asking about the
    component they pip-installed as about the site. The template documents a
    documentation template; this one has to document a component too.
    """
    from lib.constants import PYPI_URL, UPSTREAM
    from pages.legal import TERMS_DOC

    assert PYPI_URL in TERMS_DOC, "the package is not linked from its own terms"
    assert UPSTREAM["url"] in TERMS_DOC, (
        "the wrapped viewer is a separate project with its own licence and "
        "the terms must say so"
    )
    assert "MIT" in TERMS_DOC
    # And the privacy page must tell a package user that none of it applies
    # to them.
    from pages.legal import PRIVACY_DOC

    assert "The package stores nothing" in PRIVACY_DOC
