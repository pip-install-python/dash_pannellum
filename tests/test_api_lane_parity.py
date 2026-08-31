"""/api's prop table exists in EVERY lane, and these pins can go red.

THE DEFECT (sync item 18 contract 7, the FOURTH empty-/api mechanism;
muicharts note 80): a markdown2dash directive that renders Dash components
puts its output only in the React tree. The machine lane, the prerender and
the crawler HTML are built from the markdown SOURCE, where the directive
line is stripped — so this host's /api served a props page with NO PROPS to
every agent and crawler while looking perfect in a browser. Measured here
2026-08-31 before the fix: 27 props in the layout, ZERO in /api/llms.txt,
the crawler HTML and the app-shell markup alike.

THE REAL DEFECT WAS THE TEST. An earlier pin (item 16's, in
test_nav_contract.py) asserted the props against the RENDERED LAYOUT — it
saw the one lane that worked, and its author noticed the crawler document
lacked them and moved the assertion rather than filing the defect. So:
assert ROWS and row CONTENT, in every lane, and mutation-check the pins.

THE BROWSER LANE IS THREE ARTIFACTS and only two are testable here: the
app-shell markup and the dimll prerender block inside the SAME received
HTML (where the fix lands) are both asserted below; the JS-rendered DOM is
not reachable from a test client and is covered by the layout pin.
"""

from __future__ import annotations

import pytest

from conftest import BROWSER_UA, CRAWLER_UA

SPEC = "dash_pannellum.DashPannellum"

# Props that exist ONLY in the component's metadata/docstring — never in
# docs/api/api.md's hand-written prose. Their presence proves the table was
# GENERATED into that lane rather than typed there.
GENERATED_ONLY = ("northOffset", "hideLoadingSpinner", "useHttpStreaming",
                  "autoLoad", "showCenterDot", "preloadScenes")


@pytest.fixture(scope="module")
def props():
    from lib.directives.kwargs import resolve_props

    return resolve_props(SPEC)


def test_the_one_parse_returns_real_rows(props):
    """Non-vacuity for everything below: if the shared parse returned [],
    every lane assertion would be comparing zero against zero."""
    assert len(props) >= 20, f"only {len(props)} props resolved from {SPEC}"
    names = {p["name"] for p in props}
    for prop in GENERATED_ONLY:
        assert prop in names, f"{prop} missing from the shared parse"


def test_every_lane_carries_every_generated_row(client, props):
    """Lane parity, on ROWS — not on a heading, and not on one lane."""
    lanes = {
        "machine /api/llms.txt": client.get("/api/llms.txt").text,
        "crawler /api": client.get("/api", user_agent=CRAWLER_UA).text,
        "app shell /api": client.get("/api", user_agent=BROWSER_UA).text,
    }
    missing = {
        lane: [p for p in GENERATED_ONLY if p not in body]
        for lane, body in lanes.items()
    }
    assert not any(missing.values()), (
        "the prop table is absent from a lane — a directive that renders "
        f"only into the React tree is the usual cause: {missing}"
    )


def test_row_CONTENT_survives_the_trip_not_just_the_name(client, props):
    """Names alone would pass on a table of empty cells. Assert a row's
    TYPE and a distinctive word from its description, in the machine lane
    (the one that was silent)."""
    body = client.get("/api/llms.txt").text
    by_name = {p["name"]: p for p in props}
    row = by_name["northOffset"]
    assert str(row["type"]).strip() in body, "the row's type did not reach the corpus"
    word = max(str(row["description"]).split(), key=len)
    assert word in body, f"no description text for northOffset reached the corpus ({word!r})"


def test_the_pins_go_red_when_the_expansion_is_disabled(monkeypatch, client):
    """THE MUTATION CHECK the item asks for by name. Disable the shared
    parse and the machine lane must lose its rows — a pin that cannot go
    red is what let this ship."""
    from pages import markdown as md

    monkeypatch.setattr(md, "_kwargs_table", lambda spec: "\n")
    page = next(f for f in __import__("pathlib").Path("docs").glob("api/*.md"))
    expanded = md._expand_source_directives(page.read_text())
    for prop in GENERATED_ONLY:
        assert prop not in expanded, (
            f"{prop} still present with the expansion disabled — this pin "
            "cannot go red, so it was never guarding anything"
        )


def test_the_directive_stays_documentation_inside_a_fence():
    """Fence-awareness, the same rule `.. source::` carries: a directive
    shown inside a ```markdown block teaches syntax and must not expand."""
    from pages.markdown import _expand_source_directives

    fenced = "```markdown\n.. kwargs::" + SPEC + "\n```\n"
    out = _expand_source_directives(fenced)
    assert ".. kwargs::" in out and "| Prop |" not in out
