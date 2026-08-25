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
