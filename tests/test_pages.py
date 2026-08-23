"""Structural pins on what every page serves to a generic client.

Ported from the boilerplate's tests/test_pages.py in the round-3 floor pass
(template 1.6.11). Deliberately NOT the whole template file: its
REQUIRED_PATHS and title/body sweeps describe the boilerplate's own page
set, and this repo already covers reachability and prose in
tests/test_llms_routes.py and tests/test_docs_content-style checks. What is
ported is the part that pins what the >=2.7.1 floor buys, plus the app-side
defect that pin discovered.
"""

from __future__ import annotations

import re


def test_prerender_single_h1_and_deduped_footer_llms_links(client, page_paths):
    """What the >=2.7.1 floor buys, pinned from the app's side, EVERY page.

    Below dimll 2.7.0 every page served TWO h1s to a generic client — the
    injected prerender header plus the doc body's own markdown H1, a
    duplicate-H1 page in every crawler's eyes. This host measured exactly
    that on 2026-08-22: two h1 on `/`, `/getting-started`,
    `/components/tours` and `/components/video`, and it could not be fixed
    fork-side, because the second h1 comes from `_build_llms_doc`'s
    `# {name}` preamble, which is CORRECT for /llms.txt (that document
    needs its own title). 2.7.0 dedups it in the package, which is why the
    floor is the fix.

    The footer half: on "/" the per-page llms.txt link equals the root's, so
    pre-2.7.0 printed it twice; subpages legitimately carry both, DISTINCT.

    The sweep also catches app-side H1 pollution — the fence-expansion class
    that `test_source_expansion_is_fence_aware` below pins directly.

    HTML comments are stripped before counting: templates/index.html carries
    a comment explaining the no-JS block that was removed, and a page's
    prose may legitimately discuss headings. Admin pages are skipped — they
    are hidden from machine surfaces and carry no prerender.
    """
    checked = 0
    for path in page_paths:
        if path.startswith("/admin"):
            continue
        html = client.get(path).text  # default UA — the universal lane
        stripped = re.sub(r"<!--.*?-->", "", html, flags=re.S)

        h1s = re.findall(r"<h1[\s>]", stripped)
        assert len(h1s) == 1, (
            f"{path}: {len(h1s)} h1 elements in the generic-lane document — "
            "either the pre-2.7.0 prerender-header duplicate or app-side "
            "markdown leaking headings (the fence-expansion class)"
        )

        footer = re.search(r"<footer.*?</footer>", stripped, re.S)
        assert footer, f"{path}: no prerender footer in the generic-lane document"
        llms_links = re.findall(r'href="([^"]*llms\.txt)"', footer.group(0))
        assert len(llms_links) == len(set(llms_links)), (
            f"{path}: duplicate llms.txt links in the prerender footer "
            f"({llms_links}) — 2.7.0 dedups the per-page link when it "
            "equals the root"
        )
        if path == "/":
            assert llms_links == ["/llms.txt"], (
                f"home footer llms links {llms_links} — expected exactly the "
                "root link once"
            )
        checked += 1

    assert checked, "no non-admin pages were swept — the fixture returned nothing"


def test_source_expansion_is_fence_aware(app):
    """A `.. source::` inside a fenced block is documentation, not a directive.

    This repo's ten `.. source::` directives are all real (none currently sit
    inside a teaching fence), so the bug does not manifest here today — but
    pages/markdown.py is a byte-copy of the template's, and the moment any
    doc here shows the syntax inside a ```markdown fence the old expansion
    would inject a ```python fence inside the already-open one, closing it
    early. From there the inlined file renders as markdown on the machine
    lane and every `# comment` line becomes an <h1> (the five-h1 finding on
    the template's tutorial page, 2026-08-23). The browser lane was never
    affected, because markdown2dash parses fences properly — which is what
    made it invisible.

    The `app` fixture is requested only so pages/markdown.py is already
    imported with the repo root as CWD.
    """
    import sys

    expand = sys.modules["pages.markdown"]._expand_source_directives

    expanded = expand(".. source::requirements.txt")
    assert "# File: requirements.txt" in expanded, "real directive not expanded"
    assert "```" in expanded, "expansion lost its fence"

    taught = "```markdown\n.. source::requirements.txt\n```"
    assert expand(taught) == taught, "a fenced example was expanded"

    tilde = "~~~\n.. source::requirements.txt\n~~~"
    assert expand(tilde) == tilde, "a tilde-fenced example was expanded"
