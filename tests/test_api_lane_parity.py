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


# ---------------------------------------------------------- the exec lane --


def test_every_exec_directive_reaches_the_machine_lane():
    """Consolidation 2, Q6: THE AXIS IS PAIRING, NOT FENCING.

    `.. exec::module` renders a component into the React tree; its SOURCE
    reaches an agent only if the page also carries a `.. source::` for the
    same file, or the exec-lane builder expands it. Measured here before
    the builder: 11 unfenced execs, ONE unpaired —
    docs/getting-started/basic_panorama.py, the first example a reader
    meets, whose code appeared in no machine lane at all.
    """
    import pathlib
    import re

    from pages.markdown import _exec_target_path, _expand_source_directives

    EXEC = re.compile(r"^\.\. exec::(.+?)$")
    checked = 0
    for f in sorted(pathlib.Path("docs").glob("*/*.md")):
        text = f.read_text()
        expanded = _expand_source_directives(text)
        fence = None
        for line in text.split("\n"):
            head = line.lstrip()[:3]
            if fence is None and head in ("```", "~~~"):
                fence = head
                continue
            if fence is not None:
                if head == fence:
                    fence = None
                continue
            m = EXEC.match(line)
            if not m:
                continue
            checked += 1
            target = _exec_target_path(m.group(1))
            assert f"# File: {target}" in expanded, (
                f"{f}: `.. exec::{m.group(1).strip()}` renders a component "
                "whose source reaches no machine lane"
            )
    assert checked >= 5, f"only {checked} exec directives seen — sweep too thin"


def test_the_exec_expansion_dedupes_on_the_TARGET_not_the_line():
    """Same target => one copy. DIFFERENT target => still expanded (the
    half a naive `already has a source::` check gets wrong)."""
    import pathlib

    from pages.markdown import _expand_source_directives

    a = sorted(pathlib.Path("docs/tours").glob("*.py"))[0]
    b = sorted(pathlib.Path("docs/scenes").glob("*.py"))[0]
    mod = str(a).replace("/", ".")[:-3]
    same = f".. exec::{mod}\n\n.. source::{a}\n"
    diff = f".. exec::{mod}\n\n.. source::{b}\n"
    assert _expand_source_directives(same).count("# File:") == 1
    assert _expand_source_directives(diff).count("# File:") == 2


def test_code_false_is_the_authors_signal_and_dedupe_outranks_it():
    """Template 1.6.43, which the template seat shipped to production and
    muischeduler caught: `:code: false` is the AUTHOR saying this module is
    plumbing for an embed, not documentation. Expanding it publishes to the
    machine lane exactly what the browser lane deliberately hides — and
    silently, because the browser keeps looking right.

    On THIS host 10 of 11 exec directives carry `:code: false`, and all ten
    also carry their own `.. source::`, so the source was already published
    by the author's explicit choice and the dedupe kept the builder silent.
    That is one authoring edit away from the defect, which is why the
    precedence is pinned rather than trusted.
    """
    from pages.markdown import _expand_source_directives as expand

    paired = (".. exec::docs.tours.tour_example\n    :code: false\n\n"
              ".. source::docs/tours/tour_example.py\n")
    hidden = ".. exec::docs.tours.tour_example\n    :code: false\n"
    plain = ".. exec::docs.tours.tour_example\n"

    # 1. dedupe OUTRANKS the marker: the source is in this document, so
    #    announcing it as withheld would be a false statement about the page
    out = expand(paired)
    assert "# File:" in out and "source withheld" not in out

    # 2. withheld -> a MARKER naming the module, never the source and never
    #    a silent skip: broken, hidden and absent must not look alike
    out = expand(hidden)
    assert "# File:" not in out, "the author's withheld source was published"
    assert "source withheld" in out and "tour_example.py" in out

    # 3. no signal -> expand, which is the mechanism-4 fix
    assert "# File:" in expand(plain)


def test_no_withheld_source_is_published_by_any_real_page():
    """The live form of the pin above, over the actual docs tree."""
    import pathlib
    import re

    from pages.markdown import _exec_target_path, _expand_source_directives

    EXEC = re.compile(r"^\.\. exec::(.+?)$")
    SRC = re.compile(r"^\.\. source::(.+?)$")
    checked = 0
    for f in sorted(pathlib.Path("docs").glob("*/*.md")):
        lines = f.read_text().split("\n")
        sourced = {m.group(1).strip() for m in (SRC.match(x) for x in lines) if m}
        expanded = _expand_source_directives(f.read_text())
        for i, line in enumerate(lines):
            m = EXEC.match(line)
            if not m:
                continue
            opts = []
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if s.startswith(":"):
                    opts.append(s)
                elif not s:
                    continue
                else:
                    break
            if not any(o.replace(" ", "").lower() == ":code:false" for o in opts):
                continue
            checked += 1
            target = _exec_target_path(m.group(1))
            if target in sourced:
                continue  # the author published it themselves
            assert f"# File: {target}" not in expanded, (
                f"{f}: `:code: false` withheld {target} and the builder "
                "published it to the machine lane anyway"
            )
    assert checked >= 5, f"only {checked} withheld directives seen — sweep too thin"
