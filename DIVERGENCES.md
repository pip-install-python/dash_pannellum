# Divergences from the template

Every DELIBERATE difference between this repo and
dash-documentation-boilerplate, with its reason. This file is the
boundary between design and drift:

- Template syncs read this file FIRST and must not "restore" anything
  recorded here.
- A difference not recorded here is treated as drift and will be
  synced away.
- Record the divergence in the SAME commit that creates it — one
  line: what differs, why, and what the template would otherwise do.
- An empty list is a statement too: it means this repo intends to
  match the template exactly.

Fleet precedents for what belongs here: flexlayout's own-source
`_build_llms_doc` dedup and app-key sourcing; flows' own
`_health_body` payload shape (ports the healthz CONTRACT, not the
template's file); clerkhook's minimal `{ok, app, build}` healthz and
its heartbeat-as-before_request (the single anonymous 200 on a locked
host); muischeduler's no-npm dependabot scope.

**Not divergences, stated once so a sync does not mistake them for
drift:** this repo is the `dash-pannellum` COMPONENT as well as its
documentation site, so `src/`, `dash_pannellum/`, `package.json`,
`webpack.config.js` and `.github/workflows/release.yml` have no
template counterpart — they are additional, not different. Per-fork
values (host, brand, page set, port 8561, image name, social card)
are the fork ritual, not divergences.

One consequence of that extra half is worth stating outright, because
it looks exactly like drift: **this repo has TWO Pythons on purpose.**
The SITE lane — `ci.yml`, `cd.yml`, the Dockerfile, render.yaml — is
pinned to the fleet Python (3.14, template spec 1.6.27/1.6.28 item 5)
and `tests/test_python_version.py` holds every one of those encodings
to the image's `FROM` minor. The PACKAGE lane — `release.yml`, which
verifies the tag and builds the `dash-pannellum` wheel for PyPI —
stays on its own pin and is deliberately NOT scanned by that test. The
wheel is pure Python and its audience is every Dash user's
environment, not this container; the spec says a package matrix is the
package's business. A sync that "aligns" release.yml to the container
base has conflated the two lanes, which is the defect item 5 exists to
prevent, not the fix.

## This repo's divergences

1. **`/healthz` publishes a `reporting` field** — `{..., "reporting":
   true|false}`, true when `CROSS_APP_WEBHOOK_SECRET` is set. The
   template's payload has no such field. Kept because the fleet
   battery asserts on it and because "is the hourly rollup able to
   POST at all?" is otherwise invisible from outside. Two consequences
   a sync must not undo: `lib/health.py` defines its own
   `reporting_enabled()` rather than importing
   `satellite_reporter._secret()` (that module is a byte-copy target,
   and importing a private name across it would break silently on the
   next sync), and `HealthResponse` in `lib/asgi_routes.py` declares
   `reporting` — Pydantic drops undeclared keys, and this host runs
   `DASH_BACKEND=fastapi` in production, so the typed route is the one
   the hub actually sweeps. Everything else in the payload is the
   template's contract, unchanged.

2. **The home page is hand-written, not built by the docs pipeline.**
   `pages/home.py` registers `/` and serves `pages/home.md` verbatim as
   its module-level `LLMS_DOC`; `pages/markdown.py` builds only the
   `docs/*/*.md` pages. Consequence: the template's
   `lib/page_visibility.published_name()` helper does not exist here
   and `pages/markdown.py` passes `metadata.name` directly. The
   contract that helper exists to satisfy (template 1.6.16 item 8 —
   the name the machine lane publishes at `/` is the site brand) is
   met structurally instead: `pages/home.md`'s own H1 IS
   `lib.constants.SITE_BRAND`. Measured 2026-08-25 — the generic lane
   at `/` serves exactly one `<h1>`, `dash-pannellum — 360° panoramas
   for Dash`, and `/llms.txt`'s first line is the same string.
   `tests/test_pages.py`'s sweep pins it. Porting `published_name()`
   here would add a helper with no caller.

3. **`tests/test_pages.py` is a deliberate PARTIAL port** of the
   template's file (template 1.6.11). Ported: the every-page single-h1
   + deduped-footer sweep and the fence-awareness test. Not ported:
   `REQUIRED_PATHS` and the title/body sweeps, which enumerate the
   boilerplate's own page set — this repo's reachability and prose are
   covered by `tests/test_llms_routes.py` against its own registry.
   The file's docstring says the same thing; a sync that byte-copies
   the template's version would fail on pages this site does not have.

4. **pip-audit GATES here; the template's job is advisory.**
   `continue-on-error: true` was removed 2026-08-21 once the clerk 7 /
   cryptography 50 floors made this repo's baseline quiet. Reverting is
   one line, and the job comment says so. Note for whoever reads a red
   CI: pip-audit failing is a real gate on this fork, not the advisory
   annotation it is upstream.

5. **CI's container boot passes `-e DASH_BACKEND=fastapi`.** The
   template boots the image on its Flask default. Production parity is
   the reason: `render.yaml` sets `fastapi`, so without the flag CI
   would never exercise the uvicorn worker path — the exact
   WSGI-through-uvicorn failure class the Dockerfile's CMD comment
   warns about would sail through green.

6. **The gate boot line is prefixed `[boilerplate/pannellum]`**, where
   the template prints `[boilerplate]` and this repo's nine other boot
   prints use `[dash-pannellum]`. Deliberate on both counts: the
   `boilerplate` half is the handbook's fleet-wide grep string, and the
   app key says which satellite printed it. Do not "fix" either
   direction.

7. **`/api` is this repo's OWN documentation page, not the template's
   generated one.** Template sync item 16 ships `pages/api.py`, which
   registers `/api` from `API_PACKAGES` and renders a prop table from the
   installed package's `metadata.json`. This repo has served `/api` since
   before that item — `docs/api/api.md`, whose prop table is generated from
   the SAME `metadata.json` by this repo's own `.. kwargs::` directive, plus
   curated read-only and imperative prop semantics (which prop updates when,
   which one acts on the live viewer) that a generated table cannot express.
   Shipping both would be a duplicate `/api` registration, and the generated
   one is strictly less. So `pages/api.py` is NOT in this tree.
   `lib/api_reference.py` IS — byte-identical to the template's, unused by
   the app, pinned by `tests/test_nav_contract.py` against the fixture
   package so the next fan-out's cargo cannot rot here unseen.
   `API_PACKAGES = ["dash_pannellum"]` stays set: the header's version badge
   reads it, and it is the truthful declaration of what this site documents.
   Consequence a sync must not "fix": the template's
   `test_api_page_is_not_registered_when_no_package_is_declared` asserts
   `API_PACKAGES == []` and can never hold on a component fork.

8. **RETIRED 2026-08-31 — the template took this upstream.** 1.6.43's
    `pages/changelog.py` carries the prose-body handling this fork wrote
    (the `para` item type) AND adds `_is_release_label`, which this fork
    needed and did not have: mine EXCLUDED a prose `## ` section but
    silently DROPPED its content off the timeline, where the template's
    excludes it and folds the prose into the preceding release. Over-
    inclusion announces itself; omission does not. Taken byte-for-byte, so
    this file is cargo again. Historical text follows.

    *(was)* **`pages/changelog.py` reads TWO changelog shapes.** The template's
   parser takes Keep-a-Changelog `## [2.0.0] - 2026-08-02` with `- ` bullets
   only. This repo's CHANGELOG uses `## 2.0.0 — 2026-08-02` and is
   prose-first — the 2.0.0 entry is 63 lines of prose and zero bullets — so
   the template's reader rendered every section heading with nothing under
   it. The fix is in the parser, not the changelog: both heading shapes
   (bracketed or bare, hyphen or em dash) and a `para` item type beside
   `item`/`subitem`. It carries NO fork content and is offered back to the
   template; muicharts has the same prose changelog. Until the template
   takes it, this file is not byte-cargo here.

9. **`SAME_AS` is two entries, not one.** The template sets
   `SAME_AS = [GITHUB_URL]`. This repo IS a published package, so the PyPI
   project joins the repo — the three-way loop (docs ↔ repo ↔ PyPI) is the
   strongest statement of which URL is the package's canonical docs home.
   The item's actual contract, that `GITHUB_URL` is the single source for
   the repository, is kept.

10. **`components/header.py` will never be byte-cargo here.** It carries
    this site's brand mark (`mdi:panorama-sphere-outline`, teal `#12B886`),
    its wordmark, and a `visibleFrom="sm"` breakpoint chosen because this
    header's row is one control wider than the template's. Everything item
    16 made uniform — the Other Apps menu, the version badge, the search
    from `navbar.search_data`, `aria-label`s, the GitHub icon reading
    `GITHUB_URL` — is ported into it verbatim.

11. **RETIRED 2026-08-31 by sync item 18, exactly as this entry's own
    clause said it would be.** The template now derives the hidden-path
    set from the registry and asserts EQUALITY
    (`tests/test_nav_contract.py::test_hidden_doc_paths_match_the_registered_admin_pages`),
    which subsumes both directions this fork had been pinning by hand, so
    the two bespoke tests and the `/admin/llms.txt` canary are gone and
    `HIDDEN_DOC_PATHS` is now exactly the admin pages' llms.txt twins.
    Kept as a record of what the entry was, because the removal of
    `/analytics/llms.txt` still matters: its page was deleted in
    **ac6c33f** (2026-08-02) and the check had passed vacuously for four
    weeks. Historical text follows.

    *(was)* **`scripts/network_smoke.HIDDEN_DOC_PATHS` is a CENSUS here, not the
    template's canary, and it no longer names `/analytics/llms.txt`.** The
    template ships no hidden pages, so its list is two placeholder paths
    proving `mark_hidden` still works. This host has two real ones, so the
    list is every hidden page's llms.txt twin:
    `/admin/control-board/llms.txt` and `/admin/traffic/llms.txt`, plus
    `/admin/llms.txt` kept as the prefix canary.
    `/analytics/llms.txt` is REMOVED: the page it named was deleted in
    **ac6c33f** (2026-08-02, "Remove the local /analytics/traffic dashboard
    — traffic accounting lives on the hub"), so for four weeks the check
    passed because nothing was there, not because anything was hidden.
    `tests/test_network_smoke.py` now enforces the rule in both directions
    — every `mark_hidden` page must have its twin in the list, and no
    swept path may name a page that is gone — so neither half can rot by
    prose again. The ops seat says the template will derive this list from
    the registry later; when it does, this divergence retires.

12. **`components/header.py`'s identity constants name an ICON, not an
    image.** Item 18's `LOGO_ASSET` seam moves header identity out of the
    component and into `lib/constants.py`; the template's constant is an
    image filename (`LOGO_ASSET = "ddb.png"`). This site's mark is an
    Iconify glyph, so the constants are `LOGO_ICON` / `LOGO_WIDTH` /
    `WORDMARK_COLOR` / `WORDMARK_VISIBLE_FROM` and there is no asset to
    ship. The CONTRACT is met exactly — `grep -c "12B886\|panorama-sphere"
    components/header.py` is 0, the component holds no identity of its
    own — and `WORDMARK_VISIBLE_FROM` is `sm` rather than the template's
    `xs` for the reason recorded at item 16: this header's row is one
    control wider.

13. **`scripts/audit_links.py` is a fork tool the template does not carry,
    and it had item 18's THIRD-LANE defect.** It drove a bare
    `.test_client()` — `Werkzeug/x.y`, the crawler lane at dimll >= 2.8 —
    over every registered page, so both `mark_hidden` admin pages 404'd to
    it and were reported as broken internal links. Fixed with a named
    browser-lane UA carrying the internal token (`CLIENT_UA`), and the
    crawler-lane 404 assertion landed in the SAME change per the item's
    rule that repairing the lane alone measures strictly less. The same
    pass fixed a second inherited defect: its `own_tree` pattern still
    named `Dash-Documentation-Boilerplate`, so the "unpushed" link
    classification had never matched anything in this repo.

14. **`.. kwargs::` expands into the PROSE as well as the React tree.**
    Item 18's amended contract (7) names four mechanisms for an empty
    `/api` at 200; the fourth is a markdown2dash directive whose output
    reaches only the React tree, because the machine lane, the prerender
    and the crawler HTML are built from the markdown SOURCE where the
    directive line is stripped. This host had it, and worse than the
    baseline: measured 2026-08-31, all 27 props present in the layout and
    ZERO in `/api/llms.txt`, the crawler HTML and the app-shell markup.
    The template has no counterpart because it documents no component
    package — `pages/api.py` builds DMC tables directly and never goes
    through a directive. Fix per the item's shape: `resolve_props()` in
    `lib/directives/kwargs.py` is ONE parse with two callers, and
    `pages/markdown._expand_kwargs_directives` emits a markdown table
    fence-aware, exactly as `.. source::` has always been handled here.
    `tests/test_api_lane_parity.py` pins rows, row CONTENT and all three
    reachable lanes, and mutation-checks itself.

15. **The exec-lane builder honours `:code: false`.** Ported at
    template 1.6.43 after the template seat shipped the inverted form to
    its own production and muischeduler caught it. On this host 10 of 11
    `.. exec::` directives carry `:code: false` and all ten ALSO carry
    their own `.. source::` — so the source was already published by the
    author's explicit choice, and the dedupe (which outranks the withheld
    marker, because announcing a withheld source that is visibly in the
    document would be a false statement about the page) kept the builder
    silent on every one. Measured before porting the correction, not
    assumed. The eleventh, `docs/getting-started/basic_panorama.py`,
    carries no options and is the one the builder legitimately expanded.
    Pinned both ways in `tests/test_api_lane_parity.py`.

16. **`HeadAsGetMiddleware` is PRESENT here while the template has
    retired it** (template 1.6.44 item 2). The template pinned
    `dash-improve-my-llms==2.9.4` in item 1's own commit and measured
    15/15 HEAD/GET pairs without the shim, because 2.9.4 walks the
    router and adds HEAD wherever GET is allowed — Dash's
    lifespan-registered page catch-all included. This fork's
    requirements line is held at `>=2.8.0` by the 1.6.44 seat rider
    until the fleet pin lands at 1.6.45, and item 2's own note gates
    the retirement on the PIN, not the date: below 2.9.4 the shim is
    load-bearing.

    The shim arriving here at 1.6.44 rather than 1.6.32 is DRIFT
    CORRECTED, not a new divergence. The template's docstring for the
    class names the two hosts the original defect was measured on and
    one of them is this repo — the fix was written because of
    pannellum and never ported to it. Measured here before porting,
    fastapi lane, in-process, dimll 2.8.0: **11/15 without, 15/15
    with**. `/healthz` answered 405 to HEAD on all three UAs — the
    path the 2plot.ai hub sweeps hourly — and `/` answered 405 to a
    browser UA while answering 200 to a crawler one, the prerender
    replying above the router being exactly the shadow that hides this
    defect from any single-UA check.

    A sync that reads item 2 and deletes this class must first move
    the requirements line and re-measure the fifteen pairs, with the
    disable proved non-vacuous. `tests/test_head_parity.py` holds all
    of it, and `tests/conftest.py` gained `Client.head()` — without
    which the suite structurally could not see this.

## Byte-owned paths

Paths this fork owns byte-for-byte. The F3b fan-out never overwrites
a path listed here; everything else in the spec's `sync-verbatim`
block is the template's to update mechanically. Prose above explains
divergences; this block is the machine answer.

Repo-relative paths, one per line, `#` comments, no `..`; exactly one
block. An EMPTY block means "the template owns every sync-verbatim
path here" — present so the absence is a statement. When the block
exists it is authoritative; a fork without it gets the conservative
mention heuristic (over-flags, never restores).

The block below is EMPTY on purpose. The four paths the current specs
list as `sync-verbatim` — the three `.claude/skills/*/SKILL.md` files
and `tests/test_claude_kit.py` — arrived here byte-identical to
template 1.6.23 (shasums verified at adoption, 2026-08-25) and this
fork claims none of them. Divergence 3 names `tests/test_pages.py`,
which no spec lists as a verbatim target; it is a prose divergence,
not a byte claim, and must not be read as one.

```yaml byte-owned
```

## Declared posture

The hub reads this fence instead of its own seeded table (template
1.6.30). SHAPE is all `tests/test_claude_kit.py` validates: a wrong
value is meant to be visibly wrong, and an omitted key reads as the
template default.

`healthz` and `runtime` belong to template item 9, which this fork has
NOT consumed; declaring them would publish measurements nobody took.
Item 9 stays open.

`ai_bots` is now DECLARED, and every number in it was measured on the
wire rather than copied from the tree. The history, because the shape of
this claim matters more than the claim:

- 2026-08-30T14:17Z, build 49fc205, BEFORE the flip: ClaudeBot and
  GPTBot both got 403 / 200 / 403 on `/`, `/llms.txt`, `/healthz`.
- The fence stayed silent while item 15 sat unpushed in the tree, on
  the rule that a fence describing a deploy that has not happened is
  worse than a quiet one.
- 2026-08-30T20:58Z, build d4bce44, AFTER: both UAs 200 / 200 / 200 on
  the same three paths, and `/robots.txt` carries no training stanza at
  all (with the wall retired the package emits none — absent and Allow
  are both the allow shape).

Every 403 this host ever served was its OWN middleware. There was no
edge rule to undo; the owner confirmed the Cloudflare AI-bot feature is
Enterprise-only on this plan. An earlier note in this repo's memory that
blamed Cloudflare was wrong and is corrected.

`deploy: release-branch` is the road of item 13: Render auto-deploys
`release`, and only `.github/workflows/cd.yml`'s `deploy` job writes
it — a fast-forward push of the run's own sha after the CI matrix is
green. `main` ahead of `release` is an uncertified push pending, not
drift.

```yaml posture
ai_bots: {"/": 200, "/llms.txt": 200, "/healthz": 200}
deploy: release-branch
```
