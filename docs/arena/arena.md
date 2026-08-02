---
name: Joystick Arena
description: Drive a 360° petri-dish arena with DashRCJoystick — floor tilesets composed into data-URI panoramas, steered through the 0.2.0 imperative camera
endpoint: /components/arena
package: dash_pannellum
icon: mdi:gamepad-variant
---

.. llms_copy::Joystick Arena

.. toc::

### What this is

A **limited, focused lab**: one `DashPannellum` viewer, one
[`DashRCJoystick`](https://pip-install-python.com/pip/dash_gauge) (from `dash-gauge`), and a
petri-dish **floor tileset** — the same `{z}/{x}/{y}` rasters a
`dash-leaflet2` map serves flat — turned into a place you can stand inside
and glide around. No game mechanics, no entities: just the locomotion loop,
because that's the part that stresses the component.

It exists to answer one question from the
[360 Dish Lab](https://github.com/pip-install-python) prototyping sessions: *what does
dash-pannellum need so a tileset arena feels real-time rather than
turn-based?* The answer became **0.2.0**.

### Live example

Tilt the stick to look around — that's the **`lookAt` prop**, an imperative
camera write with no viewer rebuild. Pin the stick to its rim to **glide**:
the floor re-projects into the scene's live **canvas texture**
(0.3.0's `panoramaCanvasId` + `dynamicUpdate`) on a steady cadence — the
viewer itself is *never rebuilt*, so there is no flash, no camera reset,
nothing to bake. The segmented control jumps between the three published
arena sizes (3×3 @ z15, 5×5 @ z9, 7×7 @ z3 — native-zoom blocks of the
`pip-install-python` petri tileset).

.. exec::docs.arena.arena_example
    :code: false

.. source::docs/arena/arena_example.py
    :defaultExpanded: false
    :withExpandedButton: true

### How the tileset becomes a panorama

`assets/arena360.js` does the projection, entirely client-side:

1. **Mosaic** — the N×N native-zoom tiles are drawn into one offscreen
   canvas (the floor texture). 3×3, 5×5 and 7×7 blocks are vendored under
   `assets/tilesets/dish/{z}/{x}/{y}.jpg`.
2. **Floor projection** — for every output pixel below the horizon, the
   eye-ray hits the floor at ground distance `g = eye / tan(−pitch)` along
   the pixel's bearing; sample the mosaic at that world point. Distance fog
   and an out-of-mosaic haze finish the illusion. Above the horizon: a dark
   condenser-sky gradient.
3. **Live canvas texture** — the scene is bound ONCE to a hidden 1792×896
   `<canvas>` via the scene key `panoramaCanvasId`; with `dynamicUpdate=True`
   the sphere re-reads it every frame (Pannellum's dynamic mode — the same
   machinery as 360° video). Movement is `putImageData` (~60 ms), full stop.
   No HTTP, no data URIs, no `tour` re-outputs, no rebuild.

The bearing contract matches the flat map: **yaw 0° = north = "up" on the
tileset, clockwise** — so a `dash-leaflet2` minimap and this 360 view can
share one heading.

.. admonition::Why not hotspots for movement?
    :icon: mdi:gamepad-variant
    :color: blue

    The tours pattern (scene-switch hotspots) is a *teleport* mechanic — great
    for room-to-room tours, wrong for an arena. Here hotspots are demoted to
    optional **transition pieces**; locomotion is continuous: look with
    `lookAt`, glide by re-composing the floor. If you want contacts/markers,
    `callbackHotspots` is now **live** in 0.2.0 (diffed imperatively, no
    rebuild), so entities could drift in real time.

### What 0.2.0 + 0.3.0 added to make this work

| Need in the arena loop | Package answer |
|---|---|
| Steer the camera from a joystick | 0.2.0 `lookAt={pitch, yaw, hfov, animated}` — imperative, no rebuild |
| Keep zoom across moves | 0.2.0: `hfov` is reported back like `pitch`/`yaw` |
| Move without ANY flash or reset | 0.3.0: `panoramaCanvasId` scene + `dynamicUpdate` — redraw pixels, never rebuild |
| No white blink on the rebuilds you DO keep | 0.3.0: viewer container is transparent (was Pannellum's #f4f4f4) |
| Instant tour jumps elsewhere | 0.2.0 `preloadScenes` (default on) + `hideLoadingSpinner` |
| Real-time markers | 0.2.0: `callbackHotspots` applies via `addHotSpot`/`removeHotSpot` |
| Scene switch without rebuild | 0.2.0 `loadScene="scene-id"` |

Still on the wishlist for a later release: hotspots + viewer-config
passthrough in **multiRes** mode, and a bundled (non-CDN) Pannellum runtime.

### The movement-mechanics design, distilled

Three tiers, by how often the world changes:

```text
LOOK   (every frame)   lookAt prop / drag             imperative, free
MOVE   (game cadence)  redraw the panoramaCanvasId    pixels only, ~60ms,
                       canvas (dynamicUpdate=True)    no rebuild, no flash
WORLD  (rare)          re-output tour / loadScene     rebuild or scene jump —
                       (+ preloadScenes, spinner off,  cover it with a fade,
                        transparent container)         it's a real transition
```

One interaction lesson from building it: `DashRCJoystick` only emits on
*change*, so a held stick goes silent — hold-to-glide needs its own
cadence loop (`setInterval` while pinned, cleared on release). Everything
runs in `window.ARENA360` + three small `clientside_callback`s — the
server is never in the locomotion loop. A server callback only belongs
here when game state does (eating, spawning, scoring), which is exactly
where the turn-based 360 Dish Lab pattern picks up.
