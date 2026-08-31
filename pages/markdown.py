import logging
import re
from pathlib import Path
from typing import List, Optional

import dash
import dash_mantine_components as dmc
import frontmatter
from dash import html
from dash_improve_my_llms import register_page_metadata
from markdown2dash import Admonition, BlockExec, Divider, Image, create_parser
from pydantic import BaseModel, field_validator

from lib import aside
from lib.ad_client import inject_ad_into_aside
from lib.constants import OG_IMAGE_URL, PAGE_TITLE_PREFIX, NAME_CONTENT_MAP
from lib import gate_layouts, page_tiers, page_visibility
from lib.directives.headings import patch_renderer
from lib.directives.kwargs import Kwargs
from lib.directives.llms_copy import LlmsCopy
from lib.directives.source import SC
from lib.directives.toc import TOC
from lib.versions import substitute_versions

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

directory = "docs"

# read all markdown files
files = Path(directory).glob("**/*.md")


class Meta(BaseModel):
    name: str
    description: str
    endpoint: str
    package: str = "dash_pydantic_form"
    category: Optional[str] = None
    # Sidebar position within its category (sync item 16); ties break on name.
    order: int = 1000
    # A SHORT sidebar label where the page's full name is too long for the
    # column (sync item 18). Absent means the name is already short enough,
    # which is the case for every page on this host today.
    nav: Optional[str] = None
    icon: Optional[str] = None
    # Who may read this page: public | auth | admin | hidden. Absent means
    # the deployment default (PAGE_DEFAULT_TIER, else public) — see
    # lib/page_tiers.py for the tier model and why the default is open.
    # Enforced only when access control is wired in run.py.
    tier: Optional[str] = None
    # The second axis: does the machine twin (/<page>/llms.txt, crawler HTML,
    # the prerender) stay open while the interactive page is gated? Absent
    # defers to LLMS_PUBLIC_DEFAULT (unset = open — the data-window posture).
    # Only meaningful on `auth` pages; see lib/page_tiers.get_llms_public.
    llms_public: Optional[bool] = None
    # schema.org @type for the crawler document's JSON-LD. Absent means
    # TechArticle — every page here documents software, and "WebPage" (the
    # package default) tells Google nothing it did not already know. The
    # home page declares SoftwareApplication in run.py.
    schema_type: Optional[str] = None
    # Sitemap <lastmod>, YYYY-MM-DD, emitted VERBATIM by dash-improve-my-llms
    # >= 2.6.0 — and omitted entirely when absent. Truth or silence: set it
    # when the page's content genuinely changes (the frontmatter edit rides
    # the same commit as the prose), never script it from file mtimes, which
    # reset on every Docker build and would re-invent the daily-lie sitemap
    # 2.6.0 exists to end. The validator exists because YAML parses a bare
    # `lastmod: 2026-08-19` into datetime.date before pydantic ever sees it.
    lastmod: Optional[str] = None

    @field_validator("lastmod", mode="before")
    @classmethod
    def _lastmod_to_iso(cls, value):
        return value.isoformat() if hasattr(value, "isoformat") else value


_SOURCE_DIRECTIVE = re.compile(r'^\.\. source::(.+?)$', re.MULTILINE)
_LANG_MAP = {
    'py': 'python', 'pyi': 'python',
    'js': 'javascript', 'jsx': 'jsx',
    'ts': 'typescript', 'tsx': 'tsx',
    'css': 'css', 'scss': 'scss', 'sass': 'sass', 'less': 'less',
    'html': 'html', 'htm': 'html', 'xml': 'xml',
    'json': 'json',
    'yaml': 'yaml', 'yml': 'yaml',
    'md': 'markdown', 'rst': 'rst', 'txt': 'text',
    'sh': 'bash', 'bash': 'bash',
    'sql': 'sql', 'r': 'r',
    'toml': 'toml', 'ini': 'ini', 'conf': 'conf',
}


_KWARGS_DIRECTIVE = re.compile(r'^\.\. kwargs::(.+?)$', re.MULTILINE)
_EXEC_DIRECTIVE = re.compile(r'^\.\. exec::(.+?)$', re.MULTILINE)


def _exec_target_path(module_spec: str) -> str:
    """`docs.getting-started.basic_panorama` -> `docs/getting-started/basic_panorama.py`."""
    return module_spec.strip().replace(".", "/") + ".py"


def _kwargs_table(component_spec: str) -> str:
    """The `.. kwargs::` prop table as MARKDOWN, from the one shared parse.

    Sync item 18 contract (7), the FOURTH empty-/api mechanism: a
    markdown2dash directive that renders Dash components puts its output
    only in the React tree. The machine lane, the prerender and the crawler
    HTML are all built from the markdown SOURCE, where the directive line is
    simply stripped — so /api served a props page with NO PROPS to every
    agent and crawler while looking perfect in a browser. Measured here
    2026-08-31 before this expansion existed: 27 props in the layout, zero
    in /api/llms.txt, the crawler HTML and the app-shell markup.
    """
    from lib.directives.kwargs import resolve_props

    props = resolve_props(component_spec.strip())
    if not props:
        # Say so rather than rendering silence — an empty table and a broken
        # spec looked identical, which is how this survived a release.
        return f'\n<!-- kwargs: no props resolved for {component_spec.strip()} -->\n'
    rows = ["| Prop | Type | Description |", "|------|------|-------------|"]
    for prop in props:
        name = str(prop.get("name", "")).strip()
        typ = str(prop.get("type", "")).strip().replace("|", "\\|")
        desc = " ".join(str(prop.get("description", "")).split()).replace("|", "\\|")
        rows.append(f"| `{name}` | {typ} | {desc} |")
    return "\n" + "\n".join(rows) + "\n"


def _expand_source_directives(markdown_content: str) -> str:
    """Inline `.. source::path` directives with the referenced file content.

    This produces the prose that dash-improve-my-llms 2.0 will serve at
    `/<page>/llms.txt`. Replacing the directive with the real file content
    is what makes the LLM output self-contained for the "paste into a chat
    window" audience.

    FENCE-AWARE, and it has to be: a directive INSIDE a fenced code block
    is documentation showing the syntax, not a directive (docs/example and
    docs/directives both teach `.. source::` inside ```markdown fences).
    Expanding it injects a ```python fence inside the already-open fence,
    which CLOSES it early — from there the inlined file renders as
    markdown, every `# comment` line becomes an <h1>, and the machine lane
    of the page serves broken structure (found 2026-08-23 by the
    single-h1 pin in tests/test_pages.py; the browser lane was never
    affected because markdown2dash parses fences properly).
    """
    def expansion(directive_line: str) -> str:
        file_path = _SOURCE_DIRECTIVE.match(directive_line).group(1).strip()
        try:
            full = Path(file_path)
            content = full.read_text()
            ext = full.suffix.lstrip('.').lower()
            lang = _LANG_MAP.get(ext, ext or 'text')
            tail = '' if content.endswith('\n') else '\n'
            return f'\n```{lang}\n# File: {file_path}\n\n{content}{tail}```\n'
        except FileNotFoundError:
            return f'\n<!-- Error: File not found: {file_path} -->\n'
        except Exception as exc:
            return f'\n<!-- Error reading {file_path}: {exc} -->\n'

    # Targets that already have a `.. source::` of their own, so the exec
    # expansion below can DEDUPE against them (ops' rule): same target =>
    # skip, DIFFERENT target => still expand. Collected unfenced only, for
    # the same reason the expansion is fence-aware.
    sourced = set()
    _fence = None
    for _line in markdown_content.split('\n'):
        _head = _line.lstrip()[:3]
        if _fence is None and _head in ('```', '~~~'):
            _fence = _head
        elif _fence is not None and _head == _fence:
            _fence = None
        elif _fence is None:
            _m = _SOURCE_DIRECTIVE.match(_line)
            if _m:
                sourced.add(_m.group(1).strip())

    out: List[str] = []
    fence = None  # the marker that opened the block we are inside, if any
    lines = markdown_content.split('\n')
    for i, line in enumerate(lines):
        head = line.lstrip()[:3]
        if fence is None and head in ('```', '~~~'):
            fence = head
        elif fence is not None and head == fence:
            fence = None
        elif fence is None and _SOURCE_DIRECTIVE.match(line):
            out.append(expansion(line))
            continue
        elif fence is None and _EXEC_DIRECTIVE.match(line):
            # `.. exec::module` renders a COMPONENT into the React tree; its
            # source never reaches the machine lane unless it is expanded
            # here. THREE OUTCOMES, and the PRECEDENCE is the whole lesson
            # (template 1.6.43, found by muischeduler after the template
            # shipped the inversion to production):
            #
            #  1. Target already `.. source::`d in this document -> SILENT.
            #     Dedupe wins over the withheld marker: the source IS here,
            #     so announcing it as withheld would be a false statement
            #     about the page. On THIS host that is 10 of 11 directives.
            #  2. `:code: false` -> a MARKER naming the module, never the
            #     source and never a silent skip. That option is the AUTHOR
            #     saying "this module is plumbing for an embed, not
            #     documentation"; expanding it publishes to the machine lane
            #     exactly what the browser lane deliberately hides, and does
            #     it silently, because the browser keeps looking right.
            #     Broken, hidden and absent must not look alike.
            #  3. Otherwise -> expand, which is the mechanism-4 fix.
            spec = _EXEC_DIRECTIVE.match(line).group(1)
            target = _exec_target_path(spec)
            opts = []
            for nxt in lines[i + 1:]:
                stripped = nxt.strip()
                if stripped.startswith(':'):
                    opts.append(stripped)
                elif not stripped:
                    continue
                else:
                    break
            hidden = any(o.replace(' ', '').lower() == ':code:false' for o in opts)
            out.append(line)
            if target in sourced:
                pass
            elif hidden:
                out.append(
                    f'\n<!-- component rendered from {target}; source withheld '
                    f'by `:code: false` -->\n'
                )
            else:
                out.append(expansion(f'.. source::{target}'))
            continue
        elif fence is None and _KWARGS_DIRECTIVE.match(line):
            # Same fence rule and the same reason: `.. kwargs::` inside a
            # ```markdown block is documentation showing the syntax.
            out.append(_kwargs_table(_KWARGS_DIRECTIVE.match(line).group(1)))
            continue
        out.append(line)
    return '\n'.join(out)


def _build_llms_doc(name: str, description: str, expanded_markdown: str, path: str) -> str:
    """Wrap the expanded markdown with the heading/description preamble that
    /llms.txt readers expect."""
    parts: List[str] = [f"# {name}\n"]
    if description:
        parts.append(f"> {description}\n")
    parts.append("---\n")
    parts.append(expanded_markdown.rstrip() + "\n")
    parts.append("\n---\n")
    parts.append(f"*Source: {path}*\n")
    return "\n".join(parts)


# Headings containing inline code/emphasis crash markdown2dash's renderer and,
# when they don't, get an id their own TOC anchor doesn't match. Must run
# before create_parser() instantiates the renderer. See lib/directives/headings.
patch_renderer()

directives = [Admonition(), BlockExec(), Divider(), Image(), Kwargs(), LlmsCopy(), SC(), TOC()]
parse = create_parser(directives)

for file in files:
    logger.info("Loading %s..", file)
    metadata, content = frontmatter.parse(file.read_text())
    metadata = Meta(**metadata)

    # Substitute derived facts BEFORE any consumer sees the text, so the
    # browser page, the copy button, and /<page>/llms.txt all publish the
    # same truth. A doc writes {{VERSION:<distribution>}} instead of a
    # version number — any installed package, so a satellite documents its
    # own component library the same way. See lib/versions.py for why.
    content = substitute_versions(content, source=str(file))

    # Store raw markdown content in NAME_CONTENT_MAP for the LLM copy button.
    NAME_CONTENT_MAP[metadata.name] = content

    # Pages with a `.. toc::` fill the aside; the shell collapses it for
    # every other page (lib/aside.py, sync item 16 — full-width /changelog).
    if ".. toc::" in content:
        aside.register(metadata.endpoint)

    layout = parse(content)

    # add heading and description to the layout
    section = [
        dmc.Title(metadata.name, order=2, className="m2d-heading"),
        dmc.Text(metadata.description, className="m2d-paragraph"),
    ]
    layout = section + layout

    # 2plot.dev ad network: append the ad slot below the TOC links inside
    # the page's aside (pages without `.. toc::` simply get no ad).
    inject_ad_into_aside(layout, metadata.endpoint)

    # Wrap the whole page in ONE container with a page-unique id. dash-renderer
    # keys React children by component id, and markdown2dash gives every heading
    # an id derived from its text ("usage", "introduction", ...) so TOC anchors
    # work. Those ids repeat within and across pages, so when fast navigation
    # swaps _pages_content.children between two flat layout lists, React
    # reconciles by colliding keys and splices stale headings from the previous
    # page into the new one (TOC-only ghost page until you scroll). A single
    # keyed wrapper per page makes every swap old-node -> new-node: atomic
    # unmount/mount, no cross-page key matching. Do not flatten this back into
    # a list.
    layout = html.Div(
        layout, id="m2d-page" + metadata.endpoint.replace("/", "-")
    )

    # register with dash — the layout goes in behind the interactive gate.
    # The tree is still built once, above; gated_layout only decides per
    # render whether the visitor gets it or the sign-in/forbidden/404 card
    # (lib/gate_layouts.py). With every tier public the verdict is a dict
    # lookup that always says allow, so an ungated fork pays ~nothing.
    dash.register_page(
        metadata.name,
        metadata.endpoint,
        name=metadata.name,
        title=PAGE_TITLE_PREFIX + metadata.name,
        description=metadata.description,
        layout=gate_layouts.gated_layout(
            metadata.endpoint, metadata.name, layout
        ),
        category=metadata.category,
        order=metadata.order,
        nav=metadata.nav,
        icon=metadata.icon,
        # Without this Dash infers an image from assets/ by reaching for
        # `logo.<ext>` — an SVG, which every social scraper rejects — and emits
        # it ALONGSIDE the og:image in templates/index.html. This fork dropped
        # the template's `assets/logo.svg` in the gate-wave pass, so there is
        # nothing left to infer today; the explicit URL stays as the guard, so
        # re-adding any `logo.*` asset can never silently change the unfurl.
        # See lib.constants.OG_IMAGE_URL.
        image_url=OG_IMAGE_URL,
    )

    # Feed the expanded markdown into dash-improve-my-llms so /<page>/llms.txt
    # serves the directive-expanded prose. This replaces the custom Flask
    # route that used to live in run.py and works across all three backends.
    # Record the declared tier before the prose is registered, so a gate can
    # never be applied later than the content it is meant to gate.
    #
    # ONE declared value, TWO ledgers. The control board's row first —
    # overrides written there win at resolution time (lib.access.local_tier),
    # which is what makes a board toggle apply live. Then the network ledger:
    # what the hub's tier ceiling compares against and what lib.access
    # enforces underneath any override.
    page_visibility.register_default(metadata.endpoint, metadata.name,
                                     visibility=metadata.tier,
                                     llms_public=metadata.llms_public)
    page_tiers.register(metadata.endpoint, metadata.tier,
                        llms_public=metadata.llms_public)

    expanded = _expand_source_directives(content)
    # The full record, matching the dash.register_page call above. These two
    # calls must never describe the same page differently: the thinner record
    # here is exactly how the fleet shipped "dash-leaflet2 | Attribution" to
    # browsers and a bare "Attribution" to Google (the one bug behind every
    # SEO defect measured across the network, 2026-08). title and image_url
    # are read by dash-improve-my-llms 2.5.0+; older packages ignore them.
    register_page_metadata(
        path=metadata.endpoint,
        name=metadata.name,
        description=metadata.description,
        title=PAGE_TITLE_PREFIX + metadata.name,
        image_url=OG_IMAGE_URL,
        schema_type=metadata.schema_type or "TechArticle",
        # Pre-2.6 packages swallow this into **kwargs and ignore it (no
        # TypeError — measured on 2.5.1); the floor in run.py guarantees
        # >= 2.6.0, where a real date is emitted and None omits the tag.
        lastmod=metadata.lastmod,
        llms_doc=_build_llms_doc(metadata.name, metadata.description, expanded, metadata.endpoint),
    )
