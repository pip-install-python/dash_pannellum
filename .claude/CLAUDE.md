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
- `/healthz` build == HEAD **of `release`** is the deploy proof on this
  release-branch host — read the fuller trap further down before acting
  on this line. Written unqualified here until 2026-09-05, when item
  14's counter showed the two lines sitting 20-odd entries apart: a
  reader who met this one first was sent to the wrong ref, and `main`
  ahead of `release` reads as drift instead of what it is (an
  uncertified push pending). A missing geo block on dimll ≥2.7 means
  the cache trap fired (unless DIVERGENCES.md says this host's healthz
  is deliberately minimal). The general form, since this file is now
  long enough to contain its own contradictions: when a trap is later
  corrected, AMEND THE ORIGINAL — a correction that only appends
  leaves the wrong answer in the place a reader looks first.
- Always GET, never HEAD — and the mechanism, which the fleet got wrong
  through two rounds of diagnoses before measuring it, and which was
  re-measured here 2026-09-05. HEAD responses omit the Link headers,
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
  GET THE LAYER RIGHT — two rounds of fleet diagnoses said "Starlette"
  and three probes went looking in the wrong package.
  `starlette.routing.Route` DOES add HEAD wherever GET is present
  (`self.methods.add("HEAD")`, the same courtesy Werkzeug does); it is
  FastAPI's `APIRoute` that takes `methods` literally, which is why a
  route declared `@router.get(...)` returns 405. A HEAD probe therefore
  tells you about the ROUTER'S METHOD TABLE and never about the
  document. GET is never wrong.
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
  unmoved and the wire unchanged.
  THE SAMPLER IS WRITTEN NOW (1.6.44 item 17), so the next promote does
  not need anyone to re-derive the method under time pressure:
  `python3 scripts/promote_sampler.py --sha <sha>` — eight samples at 45
  second intervals, started FROM THE MOMENT OF THE PUSH. Three things a
  hand-written watcher gets wrong and this does not.
  ONE LOOP, ONE TIMELINE: the wire and the run state are read in the same
  iteration, because two separate reconstructions invite exactly the
  arithmetic error the measurement exists to avoid.
  TIME AGAINST THE PROMOTE STEP'S `completed_at`, never the deploy JOB's
  — the job CONTAINS the build-match wait, so it completes when the wait
  SEES the swap and therefore tracks the swap, not the promote; on the
  template's two measured pairs it landed at -13s and 0s, useless either
  way.
  RETRY EACH SAMPLE and record `unreadable` as a state DISTINCT from
  `old`: the container restart lands exactly where the bracket needs its
  sample (twice out of two on the template), so an un-retried loop is
  systematically blind at the only moment that matters, and folding
  unreadable into old invents a bracket nobody observed. The sampler
  REFUSES to report a bracket it did not observe — a single "new" sample
  cannot say what it followed.
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
- A DETECT OVER PROSE PARSES, OR IT STRIPS COMMENTS **AND STRINGS** —
  and over Markdown it FLATTENS WHITESPACE and reads CASE-INSENSITIVELY
  (1.6.44 item 13). Three shapes, all of which produce a confident
  wrong answer:
  (1) a raw grep matches the COMMENT explaining the absence of the
      thing it hunts. Reproduced in this round: the item-6 menu pin
      searched for `trigger="hover"` and went red on the comment above
      the fix describing the defect it replaced. Stripping comments is
      NOT the fix — a live DOCSTRING is a string, not a comment, and
      passes a comment strip untouched. The progression is raw grep ->
      comment strip -> `ast.parse`, and only the third is right: walk
      for ClassDef/FunctionDef names and Name/Attribute ids, then
      assert the parse found definitions at all, so an unreadable file
      cannot pass as a clean one.
  (2) case. A fragment written in a spec's emphasis caps and shipped in
      sentence case reads 0 both ways round.
  (3) FORMATTING. Measured on THIS repo 2026-09-05, and it is the
      instance worth remembering because the trap was correctly ported
      and the detect still said no: SYNC-1.6.43's
      `grep -ci "measured on a green push" .claude/CLAUDE.md` returns
      **0** here, because the phrase wraps a line and carries `**`
      emphasis inside it — `**measured on a GREEN\n  push**`. Flattened
      to single spaces it is 1, as are the other three fragments of
      that item. Flatten whitespace before matching prose; a Markdown
      fragment's line breaks are the renderer's, not the author's.
  Why this class recurs: a good comment explains the absence of the
  thing a detect hunts, so the better-documented the code, the more
  reliably a raw grep reports the defect it documents the absence of.
  The detects most likely to be wrong are the ones on the
  best-explained code.

#### Fleet traps merged at 1.6.44 item 14

This section was 14 entries against the template's 28 when
`scripts/kit_traps.py` was first run here. The kit is contract-class,
so no sync copies it and nothing printed the gap — a fork can be
acting on a fact the fleet retired months ago. These are MERGED, not
installed over; where this host's shape differs, the entry says so.

- A FORK'S TRAPS SECTION DRIFTS BEHIND THE TEMPLATE'S SILENTLY (1.6.44
  item 14, emojimart 166e33a). Detect, printed as a PAIR:
  `python3 scripts/kit_traps.py` reports `fork N / template M` and
  names what is missing. This fork's own first reading was **14 / 28**.
  Matching is by token overlap of each trap's opening sentence, not by
  exact text, because a fork is EXPECTED to merge a trap into its own
  wording — the check exists to find a trap that never arrived, never
  to police prose, and a strict check would train forks to paste over
  their own adaptations. Note the counter is generous in the other
  direction too: it reported this host's release-branch trap as missing
  when a fuller version of it was present under different wording, so
  read the MISSING list before acting on it.
- Any throwaway Python probe a session writes against a production host
  needs the certifi SSL context AND a retry guard. Fixing the shipped
  tools does not cover the next ad-hoc script — a seat hit
  `CERTIFICATE_VERIFY_FAILED` in a hand-written CD watcher an hour
  after shipping that exact fix inside both live tools, and another hit
  it plus an `IncompleteRead` on a chunked response in one session. A
  seat habit, not a repo contract, which is what this file is for.
- SUPERSESSION: cd.yml's build-match wait cannot tell "not deployed
  yet" from "already replaced" — both look like a live build that is
  not the sha it wants. A bot-merged PR lands with ZERO workflow runs
  on the merge sha (anti-recursion) yet still reaches production,
  because the deploy hook builds branch HEAD; two human pushes inside
  one deploy window, or hook dispatch lag, produce the same state. The
  wait fails FAST when the live build is a DESCENDANT of the wanted sha
  (compare API) rather than going red at timeout — that is the
  diagnosis, and it works whoever merged.
- Anonymous api.github.com is 60 requests/hour. With no `gh` and no
  token, read a run ONCE after CI's own jobs report complete — a blind
  20 s poll loop spends the whole budget reading rate-limit bodies as
  "not done yet". THIS SEAT HAS NO `gh` AT ALL (`command not found`),
  so this is the live condition here, not a contingency.
- A GitHub API JSON body WITHOUT the field you asked for
  (`workflow_runs` absent, not empty) is a rate-limit error body, never
  an empty result — check the field exists before trusting the answer.
- `git fetch` before any audit: the fan-out pushes to these repos now,
  and a checkout current yesterday is 2–3 merges behind origin/main
  today.
- A failed STEP is not a failed RUN. A job with
  `continue-on-error: true` reports its step red and the RUN still
  concludes `success`; the reverse bites too — a green-looking job list
  under a run whose conclusion is `failure`. Read the run's
  `conclusion`, then the annotations; never infer either from the
  other.
- Never round-trip JSON through zsh `echo` — it interprets the `\n`
  inside a multi-line commit message and hands the parser real control
  characters. Pipe curl straight into `python3`, or use `printf '%s'`.
  (This seat's shell IS zsh.)
- Repeated HTTP headers survive only if you keep them: both
  `dict(resp.headers)` and `{k: v for k, v in resp.headers.items()}`
  keep the LAST value per name, and dimll emits several `Link`
  headers. Iterate the items or ask for `get_all(name)`; in curl,
  `-D -` and read the raw block. `scripts/network_smoke.py`'s
  `_Headers` is this repo's implementation (1.6.44 item 5) — and
  `get_all()` is necessary and NOT sufficient, because over HTTP/2
  this host's edge serves both discovery relations comma-FOLDED in one
  header. Parse the relations out of the values.
- Name the crawler UA when you probe the machine lane. Which document a
  host serves is decided by the package's UA classification, not by the
  absence of a UA: curl's default `curl/8.x` receives the crawler
  document while a Chrome UA gets the app shell. Either lane can be the
  one you did not mean to test, so send `-A "<a real crawler UA>"` and
  confirm from the BODY which document came back.
- Headless browsers are CRAWLER-lane from dash-improve-my-llms 2.9.0
  (`HeadlessChrome/…` and Playwright UAs classify
  `lane: crawler, bot_type: monitor, vendor_key: headless`; 2.8.0 said
  browser). A host that screenshots ITSELF for social cards now
  receives the crawler document unless the screenshot service sends a
  non-headless UA. THIS REPO SCREENSHOTS ITSELF —
  `scripts/make_social_card.py` — so if a card goes blank or textual
  after a floor bump, look here before the template. It has not fired
  yet only because this fork is still on 2.8.0.
- And the same family one turn later, MEASURED TWICE by two seats
  within an hour, so it is a property of the technique and not one
  seat's slip: extracting a package constant with
  `re.search(r"EVENT_FIELDS = \((.*?)\)", src, re.S)` truncated at a
  `)` inside a COMMENT in the middle of the tuple, printed eight of
  sixteen fields, and reported `'ua' present: False` — confidently,
  with a number beside it. When you parse a language construct out of
  source with a regex, check the count against something independent
  before you believe a negative.
- A shell's CWD can shadow an installed package, and it produces the
  most convincing wrong answer of the family: measuring `EVENT_FIELDS`
  across two dimll versions with the cwd inside an unpacked wheel made
  `import dash_improve_my_llms` resolve from the CURRENT DIRECTORY, and
  two readings of ONE wheel were reported as two versions agreeing — in
  a CHANGELOG and a shipped spec. The load-bearing half was true and
  the supporting detail was invented. When comparing versions,
  `print(mod.__file__)` and assert it is the path you meant. IMPORT THE
  THING; parsing the constant out of source is not the safe
  alternative, it is the trap above.
- A VERIFY VERDICT IS METERING EVIDENCE, NEVER SOLE AUTHORISATION
  (1.6.44 item 18; the security incident of 2026-09-02, hub 0.26.0 ->
  0.26.1, 2plot.dev `5ca793c`). The hub gated two admin-data routes on
  2plot.dev's `/api/agent-key/verify`, whose all-unknown-tier fallback
  answered "allow" WITHOUT READING THE KEY; the lane was open
  00:52-01:16Z. The contract: a host's own data is gated by a secret
  THAT HOST HOLDS. A verify verdict may be a second factor, and it is
  metering evidence first. A new tier is UNVERIFIED until the authority
  learns it, so "ask the authority" is the wrong SHAPE for a gate — the
  failure mode of an unreachable or ignorant authority must be closed,
  and an authority that answers "allow" to a question it did not
  understand is worse than no authority. On THIS host the one caller is
  `lib/access.check`'s machine-lane branch, and it is documented in
  place as metering-only with the host-held secret named beside it:
  CROSS_APP_WEBHOOK_SECRET, without which `hub_client` cannot ask and
  the answer is `gated`.
  Four traps from the same family, each paid for by a different host:
  *a test that exercises a dependency's ABSENCE is not a test of that
  dependency's policy* — bogus-key tests that refused only because the
  verifier was unreachable locally would have passed against a verifier
  that allowed everything. *A fixture cannot falsify the assumption it
  was built from.* *A defaulted argument hides its own default* — every
  test that passes the argument proves nothing about the branch that
  COMPUTES it, and the caller that omits it is usually the one in
  production; the check is "for any defaulted argument, is there a test
  that omits it?". *A test at the wrong level* — a flush test asserted
  against the inner function and passed; rewritten against the reporter
  production actually calls, it failed for an unrelated reason nobody
  had seen. Two more in the same shape: *a port takes the half it was
  looking for*, and *verified with an input the real caller does not
  use*. And: pin the GOOD rows as well as the bypass rows; reject case
  and whitespace lookalikes of a tier rather than one literal; and
  SOURCE-PIN a default, because a behavioural suite cannot see a
  restored default that pre-empts its own guard.
