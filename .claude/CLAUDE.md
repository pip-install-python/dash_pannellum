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
- Probe with GET, not HEAD — HEAD responses omit the Link headers,
  and on THIS host HEAD was also answering 405 where GET answered
  200. Measured 2026-09-05, fastapi lane, dimll 2.8.0: 11/15 pairs.
  `/healthz` 405'd to every UA and `/` 405'd to a browser UA while
  answering 200 to a crawler — the package's prerender replying
  above the router, which is why a one-UA HEAD check reads green on
  a broken host. Fixed at 1.6.44 by porting `HeadAsGetMiddleware`
  (template 1.6.32, written after a measurement on this very repo
  and never ported until now). The shim's retirement is gated on
  `dash-improve-my-llms==2.9.4`, NOT on the calendar: 2.9.4 adds
  HEAD at the route level, below it the shim is load-bearing. The
  Link-header half of this trap still stands on its own.
- Run-watchers keyed on a commit sha can match Dependabot's runs on
  the same sha — key on the workflow path (cd.yml) instead.
- The browser lane and the machine lane are different documents;
  a fix proven on one is unproven on the other.
- There is ONE classifier: `dash_improve_my_llms.classify()` (sync item
  12, dimll 2.8.0). Never add a User-Agent list to this app — the
  tracker carried one for a year (`lib/analytics_tracker.py`), it filed
  ClaudeBot as *search* when it is Anthropic's TRAINING crawler (the
  package's registry and this repo's own `run.py` comment both said so
  six lines from where the list ignored them), it still named the
  retired `anthropic-ai` / `claude-web` tokens, and it counted every
  UA-less or library client as a human. Every host in the fleet
  reported those numbers. A token the registry lacks is a pushback to
  the package seat, not a list here; `tests/test_analytics_classifier.py`
  greps the module for the old tokens and goes red if one comes back.
- `build == HEAD` on `/healthz` means HEAD of **`release`**, not main
  (sync item 13). Render deploys `release`; only cd.yml's `deploy` job
  writes it, fast-forward, after the CI matrix is green. `main` ahead of
  `release` is an uncertified push pending — its CD run is red or still
  running — never "drift" and never a reason to deploy by hand or to
  write `release` yourself (a non-fast-forward push fails the next run
  on purpose). Compare the wire against `git rev-parse origin/release`.
  Until the owner flips this service's Branch field in the Render
  dashboard, render.yaml's `branch: release` is documentation and the
  host may still build from main — the discriminating observation is
  the next push that goes red on main: `release` must not move and the
  wire must not change.
- Which branch Render actually builds can be **measured on a GREEN
  push**, by TIMING, without waiting for a red one (leaflet,
  2026-08-31 — the method, not just its answer). `main == release ==
  wire` at every step of a promote tells you NOTHING: both refs hold
  the same sha, so the wire cannot separate them, and three promotes
  on this host said nothing at all. Sample `/healthz` every ~45s from
  the moment of the push and note when the swap lands relative to the
  PROMOTE, not the push. leaflet measured build+swap at 2m03s from its
  promote; had Render reacted to the push instead, the same interval
  would have put the build live ~1m52s earlier than it appeared. That
  is STRONG EVIDENCE, not proof — a queued or slow build could produce
  the same shape. The canonical discriminator is unchanged and still
  owed here: the first push that goes RED on main must leave `release`
  unmoved and the wire unchanged. Worth taking on the next promote; it
  costs one background sampler and converts "asserted" into "strongly
  evidenced".
- **Verify the artifact the claim is about, and say which one you
  measured.** This one was earned HERE and the fleet trap names this
  host: a props table absent from the crawler document is a defect of
  the SITE, not of the harness — this repo moved that assertion onto
  the rendered layout and the pin passed for a fortnight over a corpus
  serving zero props. WHEN A LANE DISAGREES, THAT IS THE FINDING;
  never relocate the assertion to the lane that passes. The error runs
  BOTH ways and the second is worse, because it sends someone hunting
  a bug that does not exist: `curl https://…/ | grep -c skip-link`
  returns **0** on a host where the skip link ships and works
  (excalidraw), because it is a Dash component in `app.layout` — React
  renders it and the served HTML never contains it. Anything built by
  the layout rather than written into `templates/index.html` is
  invisible to the two artifacts curl can reach. The browser lane is
  THREE artifacts: the app-shell markup, the dimll prerender block
  inside the same received HTML, and the JS-rendered DOM. Name which.
- **ASSERT THE CORPUS IS NON-EMPTY before trusting any negative, and
  print the count beside the result.** A sweep that found nothing and
  a sweep that swept nothing produce the same green, and only one is
  evidence. Same family, all measured within days: a file-scoped grep
  that matched prose ABOUT the defect it was hunting; `pytest … |
  tail -2 && git commit` committing over a red suite, because a
  pipeline's exit status is the LAST command's; and a linter exiting 0
  on a directory its config excludes — not passing the file, not
  reading it. Capture the exit code; count what you swept; say both.
  On this host the two live instances were a corpus sweep reading
  `/llms.txt` alone while `/llms-small.txt` and `/llms-full.txt` went
  unswept, and a pin that passed on arrival and measured nothing.
  **A PIN THAT PASSES ON ARRIVAL IS NOT EVIDENCE IT MEASURES
  ANYTHING** — mutation-check it, or tighten it until it goes red
  once, before recording it satisfied.
- NAME THE CHECK THAT ACTUALLY RAN, not the one you meant to run (1.6.44
  item 7). `.flake8` excludes `docs/*/`, so "flake8 is clean" has never
  covered the `.. exec::` examples this site RENDERS — and on this repo
  those are the pages that showcase the component the repo ships. A file
  in `docs/` containing `def broken(:` leaves `flake8 docs/` at exit 0
  with zero output: the linter is not passing it, it is not reading it.
  Measured here 2026-09-05, alongside `py_compile` exiting 1 with the
  SyntaxError on the same file. The general form: a report says which
  invocation produced the number, over how many files, and with what
  exit code, because "lint passed" is a claim about a command and
  everyone reads it as a claim about the code. CI runs the sweep as its
  own step (`py_compile sweep of docs/`) and fails when the corpus is
  EMPTY, since a sweep of nothing is the same green as a sweep of
  something clean.
- PRINT THE RESOLVED VERSION BESIDE THE RESULT, and say which tool
  produced it (1.6.44 item 10). An acceptance is a claim about a tree
  at a version: "suite green" is not a result, "386 passed, 2 skipped,
  exit 0, dimll 2.8.0 imported from
  .venv/lib/python3.12/site-packages/dash_improve_my_llms/__init__.py"
  is. Resolve it by IMPORTING and printing `mod.__file__` — never by
  reading requirements.txt, which states the intent, and never by
  parsing source. On THIS host that rule has teeth: the requirements
  line is a `>=` floor, so the file cannot tell you what a cached
  Docker layer installed, and until `llms_version` landed on /healthz
  (1.6.44 item 1) NO surface anywhere named the version production
  serves. The gap is not theoretical — excalidraw measured
  `llms_version` 2.9.4 on the wire while its own suite ran 2.8.0, so
  its CI and its production disagreed about which package's behaviour
  every green tick was accepting.
  The same rule names the tools whose LOCAL invocation is not CI's:
  `actionlint` without shellcheck on PATH skips every `run:` block's
  shell analysis, so "actionlint clean" locally is a weaker statement
  than the CI job's; a local absence of the binary is weaker still,
  and both must be reported as what they are. The general form: when
  the check you ran differs from the check CI runs, the report says
  so in the same sentence as the result.
- A CD LANE THAT CALLS ci.yml MUST NOT ALSO LET ci.yml RUN ITSELF on a
  push to main (1.6.44 item 12, clerkhook 44c0c27). Both runs resolve to
  the concurrency group `ci-${{ github.ref }}` with
  `cancel-in-progress: true`, so one is killed at random; when the
  standalone run wins, CD's `test` job is CANCELLED, `deploy` skips,
  `release` never moves — and `main` ahead of `release` then reads as an
  ordinary pending push instead of as the accident it is, which is
  exactly the state this repo's release-branch trap tells you to treat
  as benign. Detect: `ci.yml` declares `push: branches: [main]` AND
  `cd.yml` has `uses: ./.github/workflows/ci.yml`. Acceptance: a
  `workflow_call` creates NO run of its own, so the next push to main
  adds ZERO rows to the CI workflow list and the matrix appears exactly
  once, as `ci / *` jobs INSIDE the CD run. This repo has the correct
  shape already (pull_request + workflow_dispatch + workflow_call, with
  a comment in ci.yml saying why) and the pin is in
  `tests/test_cd_promotes_release.py` so it cannot drift back.
  Sub-trap, met while writing that pin: PyYAML parses an unquoted `on:`
  key as the BOOLEAN `True`, so `workflow["on"]` raises KeyError on
  every workflow file in this repo. A test that reads triggers must try
  both keys — one that catches the KeyError and moves on asserts
  nothing at all.
