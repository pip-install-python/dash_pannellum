"""The a11y / agentic block — 1.6.44 item 6.

Five sub-items fixed, two recorded. The recorded ones are decisions and the
item's own wording allows the form; DIVERGENCES.md carries them, because a
test docstring is invisible to the fan-out and to the next sync author.

Nothing here asserts a claim it did not measure. The Dash prop check (f) and
the asset-header policy (g) are both read from the objects themselves.
"""
import re

import pytest

from conftest import REPO_ROOT


# ------------------------------------------------ (a) the network menu ------


def test_the_network_menu_opens_without_a_pointer():
    """`trigger="hover"` makes a menu pointer-only.

    The target was already a real `dmc.Button` — role=button, in the tab
    order — which is the defect one line away from the one that was actually
    there: focus it, press Enter, and nothing happened, so the only listing
    of the network in the app was keyboard-unreachable.
    """
    import ast

    # PARSED, NOT GREPPED — and this test earned that the hard way in the
    # same round item 13 codified it. The first version grepped for
    # `trigger="hover"` and went red on the COMMENT above the fix, which
    # explains the defect it replaced. A good comment describes the absence
    # of the thing a detect hunts, so the better-documented the code, the
    # more reliably a raw grep reports the defect it documents the absence
    # of. ast.parse sees values, not prose.
    tree = ast.parse((REPO_ROOT / "components" / "header.py").read_text())
    triggers = [kw.value.value for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                for kw in node.keywords
                if kw.arg == "trigger" and isinstance(kw.value, ast.Constant)]
    assert triggers, "no menu trigger declared in header.py — vacuous pin"
    assert "hover" not in triggers, (
        f"a pointer-only trigger is still declared: {triggers}"
    )
    assert "click-hover" in triggers, triggers


# ------------------------------------- (b) prose links, (c) touch targets ---


def _css() -> str:
    return (REPO_ROOT / "assets" / "main.css").read_text()


def test_prose_links_are_underlined_and_the_chrome_is_not():
    """Scoped to the page body, or the fix repaints the whole chrome.

    `#main-content` is the skip link's target, so the scope is the same one
    the keyboard path already uses rather than a second opinion about where
    the body starts.
    """
    css = _css()
    block = css.split("a11y — 1.6.44 item 6", 1)[-1]
    assert "#main-content p a" in block
    assert "text-decoration: underline" in block
    # The scope matters as much as the rule: an unscoped `a { underline }`
    # would repaint every nav row and footer icon.
    for selector in ("#main-content p a", "#main-content li a",
                     "#main-content td a", "#main-content blockquote a"):
        assert selector in block, f"missing {selector}"
    assert "\na {" not in block, "the underline rule escaped #main-content"


def test_an_icon_or_card_wrapper_link_is_not_underlined():
    block = _css().split("a11y — 1.6.44 item 6", 1)[-1]
    assert "#main-content a:has(> img)" in block
    assert "text-decoration: none" in block


def test_icon_controls_meet_44px_at_phone_width():
    """34px is what a Mantine ActionIcon size="lg" renders at; the
    iOS/Android minimum is 44."""
    block = _css().split("a11y — 1.6.44 item 6", 1)[-1]
    media = block.split("max-width: 750px", 1)
    assert len(media) == 2, "no phone-width media query in the a11y block"
    rules = media[1]
    assert "min-width: 44px" in rules and "min-height: 44px" in rules
    for target in (".mantine-AppShell-header .mantine-ActionIcon-root",
                   ".mantine-AppShell-footer .mantine-ActionIcon-root",
                   ".mantine-AppShell-header .mantine-Burger-root"):
        assert target in rules, f"{target} not widened"
    # Desktop density is deliberately unchanged — the widening must be
    # inside the media query, not above it.
    assert "min-width: 44px" not in media[0]


# ------------------------------------------------ (f) image dimensions ------


def test_dash_still_refuses_the_two_attributes_that_cannot_ship():
    """The reason (f) is width/height ONLY, re-measured rather than quoted.

    `loading="lazy"` and `decoding="async"` are not props of dash 4.4.1's
    html.Img, and Dash raises rather than passing an unknown one through —
    on the template that was 196 collection errors, not a warning. If a
    future Dash accepts them this test goes red, which is the signal to
    revisit (f), not a failure.
    """
    import inspect

    from dash import html

    names = list(inspect.signature(html.Img.__init__).parameters)
    assert "width" in names and "height" in names
    assert "loading" not in names and "decoding" not in names
    with pytest.raises(TypeError):
        html.Img(src="/assets/x.png", loading="lazy")


def test_a_local_image_gets_its_intrinsic_box_and_a_remote_one_does_not():
    """Both directions, so the sizing cannot pass as a constant.

    A wrong box is worse than no box, which is why a remote URL — a
    shields.io badge — is deliberately left unsized rather than guessed at.
    """
    pytest.importorskip("PIL", reason="Pillow is transitive here, not "
                                      "declared; CI's test job may not have it")
    from PIL import Image

    from lib.directives.headings import _SIZE_CACHE, _intrinsic_size

    local = REPO_ROOT / "assets" / "icon-art.png"
    if not local.is_file():
        pytest.skip("no local image in assets/ to measure")
    with Image.open(local) as im:
        expected = im.size

    _SIZE_CACHE.clear()
    assert _intrinsic_size("/assets/icon-art.png") == expected
    assert _intrinsic_size("https://img.shields.io/badge/x-y.svg") == (None, None)
    assert _intrinsic_size("/assets/does-not-exist.png") == (None, None)


def test_the_renderer_reserves_a_box_for_a_local_image():
    pytest.importorskip("PIL")
    from dash import html

    from lib.directives.headings import _SIZE_CACHE, patch_renderer

    local = REPO_ROOT / "assets" / "icon-art.png"
    if not local.is_file():
        pytest.skip("no local image in assets/ to measure")

    patch_renderer()
    from markdown2dash.src import renderer as m2d_renderer

    _SIZE_CACHE.clear()
    img = m2d_renderer.DashRenderer.image(None, "art", "/assets/icon-art.png")
    assert isinstance(img, html.Img)
    assert img.width and img.height, "no box reserved for a local image"
    assert img.style["maxWidth"] == "100%" and img.style["height"] == "auto", (
        "the responsive pair must stay, or the box trades layout shift for "
        "overflow"
    )

    remote = m2d_renderer.DashRenderer.image(
        None, "badge", "https://img.shields.io/badge/x-y.svg")
    assert getattr(remote, "width", None) is None


# ------------------------------------------------- (g) asset lifetimes ------


def test_only_unfingerprinted_assets_get_a_lifetime():
    from lib.static_cache import ASSET_CACHE_CONTROL, cache_control_for

    assert cache_control_for("/assets/main.css") == ASSET_CACHE_CONTROL
    assert cache_control_for("/assets/tilesets/0/0_0.jpg") == ASSET_CACHE_CONTROL
    # Documents are answers about right now. An hour of a stale one is a bug
    # report nobody can reproduce.
    for path in ("/", "/healthz", "/llms.txt", "/api/llms.txt",
                 "/admin/traffic", "/_dash-component-suites/dash/x.js"):
        assert cache_control_for(path) is None, path
    assert re.search(r"max-age=\d+", ASSET_CACHE_CONTROL)
    assert "public" in ASSET_CACHE_CONTROL


def test_both_lanes_carry_the_asset_policy():
    """The lane that SERVES here is the ASGI one, and a fix proven on the
    other is unproven on it. Both halves must exist and both must read the
    policy from lib/static_cache rather than writing a header of their own."""
    asgi = (REPO_ROOT / "lib" / "asgi_middleware.py").read_text()
    assert "class StaticCacheMiddleware" in asgi
    assert "cache_control_for" in asgi
    assert "add_middleware(StaticCacheMiddleware)" in asgi

    flask_lane = (REPO_ROOT / "run.py").read_text()
    assert "_asset_cache_lifetime" in flask_lane
    assert "cache_control_for" in flask_lane


def test_the_serving_lane_sets_the_header_on_a_real_response(client):
    """Not a source grep: the header on an actual /assets/ response."""
    response = client.get("/assets/main.css")
    if response.status != 200:
        pytest.skip(f"/assets/main.css is {response.status} under this client")
    assert "max-age=3600" in response.header("Cache-Control"), (
        f"no lifetime on /assets/main.css: {response.header('Cache-Control')!r}"
    )


def test_a_document_keeps_revalidating(client):
    assert "max-age=3600" not in client.get("/healthz").header("Cache-Control")


# ------------------------------------------- (d) and (e) are RECORDED -------


def test_the_two_recorded_subitems_are_written_down_where_a_sync_reads():
    """A test docstring is invisible to the fan-out and to the next sync.

    Item 9's whole point: nothing in a diff tells a deliberate absence from
    an accident, so the record has to be in DIVERGENCES.md.
    """
    text = (REPO_ROOT / "DIVERGENCES.md").read_text()
    flat = " ".join(text.split())
    assert "Recorded a11y decisions" in flat
    assert "1.6.44 item 6" in flat
    # (d) must say what was and was not measured FROM THIS SEAT — the trap
    # this repo earned is claiming a lane you did not read.
    assert "console" in flat.lower()
    # (e) must name the transfer encoding, which is the whole argument.
    assert "gzip" in flat.lower() or "minif" in flat.lower()
