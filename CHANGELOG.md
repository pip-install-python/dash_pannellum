# Changelog

## 0.4.1 — 2026-08-01

pannellum.2plot.dev joins the 2plot network. The component itself is
unchanged (packaging metadata modernized: SPDX license expression,
setuptools>=77); everything below is the documentation site reaching the
network standard proven on 2plot.ai, 2plot.dev, boilerplate, leaflet,
email, flexlayout and llms.

### The site now states one identity everywhere

`dash-pannellum — 360° panoramas for Dash` is the brand on every surface —
`<title>`, the /llms.txt H1, the llms viewer's chip, og:site_name, the
webmanifest, the home page H1 and the README. The package name leads
because it is the string that finds the thing on PyPI; "Pip Install
Python" is the byline, in the description. Previously every surface said
"Dash Pannellum", a name that matches no installable package.

### AI/LLM + SEO surfaces rebuilt on dash-improve-my-llms ≥ 2.3.4

The vendored 2.0.0 tarball is gone; the package installs from PyPI and
run.py refuses to boot below the 2.3.4 floor. Every `register_page` now
passes `image_url=` and `description=` — one page missing either makes
Dash emit an *empty* og:image, which scrapers prefer over every correct
tag. The social card lives on the CDN
(`cdn.2plot.ai/github_assets/pannellum.2plot.dev.png`, 1200×630), not in
assets/, so a cold container can never poison an unfurl cache.
templates/index.html declares only what Dash does not emit. The cross-host
network directory, the hub bulletin (NETWORK_BULLETIN_URL), and a real
installable-app surface (favicon set + webmanifest) are wired.

### The network's analytics contract

Requests carrying the `2plot-internal` UA token are dropped at write time,
before bot classification; every outbound call to another network host
sends that token. The hourly signed traffic rollup POSTs to 2plot.ai when
CROSS_APP_WEBHOOK_SECRET is set, under this app's one short id:
`pannellum` (AD_APP_ID, SATELLITE_APP_KEY and the bulletin app_id all
agree). /healthz answers `ok: true` on every backend — the exact field the
fleet's batteries assert.

### CI/CD is now a deploy gate

ci.yml (pull requests only; cd.yml owns main): actionlint first, a
secretless pytest suite across flask/fastapi × py3.11–3.13 × dash 4.4.0
and pinned, then the real Docker image built, fingerprint-asserted from
inside (dash ≥ 4.4, dimll ≥ 2.3.4, gunicorn ≥ 23), booted, and battered by
the same script CD runs against production. cd.yml deploys via Render
hook, waits for *sustained* health (120s settle + 5 consecutive 200s), and
runs the battery plus smoke_live against the live domain. gunicorn moved
past the request-smuggling CVEs (21.x → ≥ 23) by installing markdown2dash
`--no-deps`; the Dockerfile gained `PYTHONUNBUFFERED=1` and an explicit
COPY list. render.yaml is authored for the first deploy (docker runtime,
disk-backed analytics ledger, Clerk satellite env).

### Housekeeping

The README was rebuilt to the network standard (badges, docs links) and
made truthful again: it now lists all ten documentation pages — the old
table missed scenes, arena, emotes and gyro — and no longer claims a
vendored dash-improve-my-llms 2.0 (vendor/ holds only the dash-clerk-auth
tarball). `[project.urls]` pointed at a hyphenated repository name that
does not exist; it now points at `dash_pannellum`, with Documentation at
pannellum.2plot.dev.

The local /analytics/traffic dashboard is gone: traffic accounting lives
on the hub (the tracker and the hourly signed rollup to 2plot.ai are
unchanged), so a per-satellite dashboard was a second, staler view of the
same ledger.

tests/conftest.py removes its per-run temp state dir at exit. `mkdtemp`
falls back to the current directory when no system temp dir is writable
(sandboxed runs with TMPDIR unset), which had leaked eleven
`pannellum-tests-*` dirs into the repo root; the pattern is gitignored as
a backstop. The local `legacy/` archive — an untracked 457 MB second
clone of the original repo, whose history is already this repository's
own history — was removed from the working tree, along with stale 0.4.0
build artifacts and a 0.4.0-era forum-post draft.

## 0.4.0 — 2026-06-12

Gyro look-around — the device *is* the camera.

### Added

- **`orientation` prop** (imperative, no rebuild) — request gyroscope
  steering. Pannellum's native sensor pipeline does the quaternion work
  and runs the iOS 13+ permission prompt inside `startOrientation`; on
  iOS, set the prop from a **clientside callback on a direct tap** so the
  prompt lands inside Safari's gesture window.
- **`orientationSupported` / `orientationActive` read-only props** —
  request vs truth, kept separate on purpose: permission can be denied,
  desktops have no sensors, and Pannellum pauses gyro steering while the
  user grabs the panorama.
- **Gyro Look-Around docs page** (`/components/gyro`) — real sensor on
  phones, plus a drag-pad **tilt simulator** on desktop that feeds the
  camera the same continuous `lookAt` stream a gyroscope would.

### Notes

- Pannellum gates orientation on `DeviceOrientationEvent` + a **mobile
  user agent** + **literal `https:`** — plain-HTTP localhost reports
  unsupported even though browsers would allow the sensor there. Use a
  TLS dev cert or a tunnel to test on a phone.
- Verified end-to-end under emulated-iPhone HTTPS: support detected,
  switch engages steering, synthetic device rotation pans the camera
  (yaw 5° → −25°), disengage restores drag-only.

## 0.3.1 — 2026-06-12

Upstream feedback from the 360 Dish Lab: *"the live callbackHotspots diff
is a wholesale remove-and-re-add … an in-place positional update would let
DOM hotspots animate too."* Done.

### Changed

- **`callbackHotspots` updates are now a per-name diff** instead of a
  wholesale replace: unchanged hotspots are untouched; **position-only
  changes move the existing DOM node in place** (Pannellum re-reads
  pitch/yaw from the live spec object every render); other changes
  (text/type/cssClass) recreate just that hotspot; vanished names are
  removed. Contacts can now drift every tick as real DOM hotspots —
  staying hoverable and clickable mid-flight — instead of being redrawn
  into the canvas as a workaround.
- In-place moves trigger one render on idle viewers via `setUpdate`
  re-assertion (a same-value `setPitch` short-circuits inside Pannellum
  and renders nothing — found the hard way).

### Fixed

- **Duplicate hotspot DOM nodes** when `callbackHotspots` changed while
  the panorama was still loading: a pre-load `addHotSpot` got a second
  div from Pannellum's own load pass, leaving an orphan marker. Hotspot
  sync now waits for `isLoaded()`; the on-load sync applies the latest
  prop value.

### Added

- **Drifting-hotspot demo** on the Callback Hotspots docs page — a
  contact orbiting on a 400 ms Interval via plain prop updates, verified:
  same DOM node across the whole flight, clickable mid-drift.

## 0.3.0 — 2026-06-11

The movement-mechanics release. 0.2.0 made the camera imperative; 0.3.0
makes the **world** updatable in place — and settles the design: LOOK with
`lookAt` (free), MOVE by redrawing a canvas texture (no rebuild), rebuild
only when the WORLD changes (and treat that as a real transition).

### Added

- **Dynamic canvas scenes** — a tour scene can set `panoramaCanvasId` (the
  DOM id of a `<canvas>`) instead of a `panorama` URL. The canvas becomes
  the sphere's texture via Pannellum's dynamic mode (the same machinery as
  360° video): redraw the canvas and the view updates in place — **no
  rebuild, no camera reset, no flash**.
- **`dynamicUpdate` prop** — keeps the texture re-uploading every frame
  while a dynamic canvas scene is live.
- **Scene Configuration docs page** (`/components/scenes`) — a live config
  playground (initial-view presets, `autoRotate`, zoom limits) plus the
  **fly-to pattern**: named targets + `lookAt` with a duration, triggered
  from buttons, from clicked hotspots, and from a simulated external event.

### Fixed

- **White flash on rebuilds** — Pannellum's container defaults to
  `#f4f4f4`; the component now forces it transparent, so any rebuild dips
  to the host page's background instead of flashing white.
- **Joystick Arena flash while moving** — the arena no longer re-outputs
  `tour` per glide step (the 0.2.0 data-URI approach, which rebuilt the
  viewer every move). It binds the scene once to a live canvas and glides
  by redrawing pixels. Verified: the viewer DOM node survives whole glide
  sessions and arena switches; frame brightness stays flat (no white
  frames). Arena switches get a deliberate 140 ms dip-to-dark fade.
- **Hold-to-glide** — `DashRCJoystick` only emits on change, so a pinned
  stick went silent after one step; the arena now runs its own glide
  cadence while the stick is held at the rim.

## 0.2.0 — 2026-06-11

The real-time release — shaped by the 360 Dish Lab prototype's wishlist
(its turn-based design existed purely to work around 0.1.0's lack of an
imperative API).

### Added

- **`lookAt` prop** — imperative camera writes: `{pitch, yaw, hfov, animated}`
  pans/zooms the live viewer with **no rebuild**. Smooth enough for
  joystick-driven steering via `window.dash_clientside.set_props`.
- **`hfov` read-only prop** — the zoom now reports back alongside
  `pitch`/`yaw`, so it can be baked across rebuilds.
- **`loadScene` prop** — imperative tour scene switch, no rebuild; unknown
  IDs and the active scene are ignored.
- **`callbackHotspots` is live** — prop changes diff through Pannellum's
  `addHotSpot`/`removeHotSpot` instead of requiring a `tour` re-init, so
  markers can move in real time (360 Dish Lab wishlist #1).
- **`preloadScenes` prop (default `True`)** — other scenes' panoramas are
  prefetched once the viewer is up: tour jumps no longer show a
  "Loading..." flash.
- **`hideLoadingSpinner` prop** — suppresses Pannellum's load box per
  viewer, for preloaded tours and data-URI panoramas where the spinner is
  the only visible part of an instant transition.
- **Joystick Arena docs page** (`/components/arena`) — DashRCJoystick
  (`dash-gauge`) drives a 360° petri-dish arena composed client-side from
  vendored `{z}/{x}/{y}` floor tilesets (3×3 @ z15, 5×5 @ z9, 7×7 @ z3)
  into **data-URI panoramas**: tilt to look (`lookAt`), pin the stick to
  glide (re-compose + bake gaze). The server is never in the locomotion
  loop.

### Changed

- Callback hotspots are now applied imperatively on viewer load rather
  than baked into the scene config (no behavioral change to clicks;
  verified against the hotspots docs page).
- The Virtual Tours example demonstrates flash-free scene jumps
  (`preloadScenes` + `hideLoadingSpinner`).

### Still on the wishlist

Hotspots + viewer-config passthrough in **multiRes** mode, and a bundled
(non-CDN) Pannellum runtime.

## 0.1.0 — 2026-06-11

The revival release. The component was rebuilt for the modern Dash stack and the repository was restructured around a live documentation site.

### Breaking

- **Dash 4.2+ required.** The package now depends on `dash>=4.2.0` and is built against React 18.
- **`customControls` is coherent across modes**: `True` hides the built-in zoom/fullscreen controls in every mode. Previously it was ignored for image panoramas and inverted for video.
- **Video no longer autoplays**; users press play (browsers block autoplay-with-audio anyway).
- **`pitch`/`yaw` updates are throttled to 4/s and change-detected** (previously 10/s unconditionally). Idle viewers no longer fire callbacks.

### Added

- **Configuration props are live**: changing `tour`, `multiRes`, `video`, `autoLoad`, `compass`, `northOffset` or `useHttpStreaming` from a callback tears down and re-initializes the viewer, so panoramas can be swapped dynamically (in 0.0.6 a config change destroyed the viewer without rebuilding it).
- `loaded` is now a declared prop (it was set but undeclared in 0.0.6).
- Callback hotspots use real Pannellum `clickHandlerFunc` handlers, so `lastClickedHotspot` fires reliably.
- CDN script loading is deduplicated — multiple viewers on one page share one Pannellum/video.js load.
- Live documentation site (`run.py`) on the dash-documentation-boilerplate architecture: Dash Mantine Components appshell, markdown-driven pages with live examples, pluggable Flask/FastAPI backends, llms.txt/sitemap/robots via dash-improve-my-llms 2.0.

### Changed

- Packaging moved from `setup.py` to `pyproject.toml`; JS toolchain updated (webpack 5.97, babel 7.26, React 18.3).
- Repository restructured: component source at `src/lib/`, generated package at `dash_pannellum/`, docs app at the top level. The original 0.0.6 repo is archived untouched in `legacy/`.

## 0.0.6 — 2024

Last release of the original component (Dash 1/2 era).
