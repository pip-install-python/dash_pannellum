# dash-pannellum

## Project Overview

This repo is TWO things at once, and most mistakes here come from
forgetting the second:

1. **The component** — `dash-pannellum`, a published PyPI package
   wrapping the plug-in-free [Pannellum](https://pannellum.org/) WebGL
   viewer for Plotly Dash. React source in `src/lib/components/`,
   generated Python in `dash_pannellum/`, bundle committed.
2. **The documentation site** — `pannellum.2plot.dev`, a fork of
   dash-documentation-boilerplate that documents the component it
   ships alongside.

The template's own README describes only half of that. When a drop
says "the site", ask whether it also means the package.

Versions, dependencies and history are deliberately not restated here —
they go stale. Read `requirements.txt` for the stack, `pyproject.toml`
for the package, and `CHANGELOG.md` for what changed and when.

---

## Custom Directives

| Directive | Syntax | Purpose |
|-----------|--------|---------|
| `toc` | `.. toc::` | Generate table of contents |
| `exec` | `.. exec::module.path` | Render Python component |
| `source` | `.. source::file/path.py` | Display source code |
| `kwargs` | `.. kwargs::ComponentName` | Show component props |

Options are documented in `docs/directives/directives.md`. The
`source` expansion is fence-aware: a `.. source::` inside a ``` block
is documentation, not a directive (template 1.6.11).

---

## Configuration

### Customization Points

| File | Purpose |
|------|---------|
| `lib/constants.py` | `BASE_URL`, `SITE_BRAND`, app-wide constants — the identity source |
| `assets/main.css` | Custom CSS styles |
| `templates/index.html` | HTML template (declares only what Dash does not emit) |
| `components/appshell.py` | Theme configuration, MantineProvider settings |
| `components/navbar.py` | Navigation ordering (incl. the full-height mobile drawer) |
| `pages/home.py` + `pages/home.md` | The home page — hand-written, NOT built by `pages/markdown.py` (see DIVERGENCES.md) |
| `pages/markdown.py` | The docs pipeline: every `docs/*/*.md` page |
| `pages/control_board.py` | `/admin/control-board` — live per-page tier + llms.txt toggles (owner/admin-gated, fails closed) |
| `lib/page_visibility.py` | The board's override store (persists to `PAGE_VISIBILITY_FILE`) |
| `lib/auth_demos.py` | Live-demo teasers rendered inside the sign-in gate cards |
| `lib/health.py` + `lib/asgi_routes.py` | `/healthz` — one payload builder, three backends |

### Adding New Documentation Pages
1. Create folder in `docs/` (e.g., `docs/my-component/`)
2. Create markdown file with frontmatter:
```markdown
---
name: My Component
description: Description of my component
endpoint: /components/my-component
icon: mdi:code-tags
---

.. toc::

## Overview
...
```
3. Add Python examples as needed
4. Reference with `.. exec::docs.my-component.example`
5. Page will auto-register and appear in navigation

Every `register_page` must pass BOTH `image_url=` and `description=` —
one page missing either makes Dash emit an *empty* og:image, which
scrapers prefer over every correct tag.

### Releasing the component
Bump `pyproject.toml` + `package.json`, `npm run build`, commit, tag
`v*`, push the tag. `release.yml` publishes to PyPI via OIDC trusted
publishing and gates on tag == pyproject == package.json. The tag must
contain `release.yml` to trigger it.

---

## This host's shape (what a template-written prompt gets wrong here)

- **Production runs `DASH_BACKEND=fastapi`.** The typed `/healthz` in
  `lib/asgi_routes.py` is the one the hub sweeps — a fix proven on the
  Flask lane is unproven on the lane that serves.
- **`lib/satellite_reporter.py` is a byte-copy** of the template's and
  its `app_key()` falls back to `"boilerplate"`. `run.py` claims
  `SATELLITE_APP_KEY=pannellum` via `os.environ.setdefault` before any
  hub-facing import — never delete that line.
- **The gate boot line is prefixed `[boilerplate/pannellum]`**, not
  this repo's usual `[dash-pannellum]`. Deliberate: it is the fleet's
  grep string. Do not "fix" the inconsistency.
- **`dash-clerk-auth` is vendored**, not installed from PyPI.

---

## Resources

- [Pannellum](https://pannellum.org/)
- [Dash Documentation](https://dash.plotly.com/)
- [Dash Mantine Components](https://www.dash-mantine-components.com/)
- [dash-improve-my-llms](https://pypi.org/project/dash-improve-my-llms/)
- [Project Repository](https://github.com/pip-install-python/dash_pannellum)
- [Upstream template](https://github.com/pip-install-python/Dash-Documentation-Boilerplate)

---

## Network role & the behavioral contract

This repo is a member of the 2plot network — either the template
itself (dash-documentation-boilerplate) or a fork of it serving one
component's documentation. **Identity derives from the repo, never
from this file**: the app key comes from `SATELLITE_APP_KEY` and
run.py's fork point, the host from `lib/constants.py`'s `BASE_URL`,
the deliberate differences from the template from `DIVERGENCES.md`
at the repo root. If those disagree with anything written here,
they win.

### The contract — every session, every prompt

1. **Check the prompt against this tree before executing.** Prompts
   are written from the template's perspective and your fork may
   legitimately differ — floors, backends, payload shapes, page
   sets. A prompt step that doesn't fit this repo is a finding to
   return, not an instruction to force.
2. **Corrections are your job, not scope creep.** If a prompt's
   reference list doesn't match its steps, if its assumed state is
   wrong, or if executing it as written would produce a
   green-but-vacuous result, say so and propose the corrected
   version before running it.
3. **Verify your own deploy on the wire before reporting.** A push
   is not a result. Run `/wire-verify` (or its manual equivalent)
   against production and paste what came back. If your sandbox
   cannot reach your own domain, say exactly that — an unverified
   claim marked as unverified is honest; the same claim unmarked is
   not.
4. **Report observed versus expected, with evidence.** Paste the
   JSON, the status code, the test count. "Should work" and summary
   claims without artifacts are not reports.
5. **Divergence is legitimate when written down.** Before syncing
   template changes, read `DIVERGENCES.md`; never let a sync
   "restore" a recorded deliberate difference. When you deliberately
   diverge, record it there in the same commit — an unrecorded
   divergence is indistinguishable from drift and will be treated
   as drift.
6. **Never touch**: environment variable VALUES, hosting dashboards,
   secrets, other repos' trees, or anything the prompt didn't put in
   scope. Enumerate what you cannot do (closing PRs, dashboard
   steps) for the owner instead of claiming it done.

### Verification traps (fleet-learned, keep them)

- A `>=` floor can never pull a new release through a Docker cache
  hit — the requirements line changing IS the cache bust, and floors
  live in several encodings (requirements, run.py's boot floor,
  tests, CI): grep the number, move every one.
- `/healthz` build == HEAD is the deploy proof; a missing geo block
  on dimll ≥2.7 means the cache trap fired (unless DIVERGENCES.md
  says this host's healthz is deliberately minimal).
- Probe with GET, not HEAD — HEAD responses omit the Link headers.
- Run-watchers keyed on a commit sha can match Dependabot's runs on
  the same sha — key on the workflow path (cd.yml) instead.
- The browser lane and the machine lane are different documents;
  a fix proven on one is unproven on the other.
