---
name: Scene Configuration
description: Every Pannellum scene option passes through the tour prop — plus the lookAt fly-to pattern for event-driven camera moves
endpoint: /components/scenes
package: dash_pannellum
icon: tabler:adjustments-alt
lastmod: 2026-06-15
---

.. llms_copy::Scene Configuration

.. toc::

### How configuration flows

A scene dictionary inside `tour` is passed to Pannellum **untouched** —
anything in the [Pannellum configuration reference](https://pannellum.org/documentation/reference/)
works, even keys this page doesn't mention. Two rules of thumb:

- **Scene/world changes** (panorama, limits, autoRotate, titles) go in the
  `tour` config. Outputting a new `tour` re-initializes the viewer — since
  0.3.0 the container is transparent, so a rebuild dips to your page
  background instead of flashing white.
- **Camera-only changes** (point somewhere, zoom) use the **`lookAt`** prop —
  imperative, animated, no rebuild. That's the fly-to section below.

### Configuration playground

Live controls re-outputting the `tour` — switch the initial-view preset and
set `autoRotate` for idle cinematics:

.. exec::docs.scenes.scene_config_example
    :code: false

.. source::docs/scenes/scene_config_example.py
    :defaultExpanded: false
    :withExpandedButton: true

### The scene config vocabulary

| Key | Type | What it does |
|-----|------|--------------|
| `panorama` | str | Equirectangular image URL (or data URI) |
| `panoramaCanvasId` | str | **0.3.0** — bind the scene to a live `<canvas>` instead (see [Joystick Arena](/components/arena)) |
| `title` / `author` | str | Shown in the viewer's info bar |
| `pitch` / `yaw` / `hfov` | number | Initial camera |
| `minHfov` / `maxHfov` | number | Zoom limits |
| `minPitch` / `maxPitch` | number | Clamp vertical look (e.g. hide a tripod) |
| `minYaw` / `maxYaw` | number | Clamp horizontal look (partial panoramas) |
| `autoRotate` | number | Idle rotation in °/s; sign sets direction |
| `autoRotateInactivityDelay` | number | ms of inactivity before rotation resumes |
| `preview` | str | Image shown before load when `autoLoad=False` |
| `vaov` / `vOffset` | number | Vertical angle of view for partial panoramas |
| `backgroundColor` | [r,g,b] | Fill color around partial panoramas |
| `hotSpots` | list | Scene-switch and info hotspots ([Virtual Tours](/components/tours)) |
| `sceneFadeDuration` | number | Crossfade ms on scene change (tour `default` block) |

### Fly-to: event-driven camera triggers

The pattern you want for "*something happened — look over there*": keep a
dictionary of **named targets** (`pitch`/`yaw`/`hfov` per place), and have
any trigger — a button, a clicked hotspot, an alert from a websocket or an
`Interval` poll — output a `lookAt` with a duration. Pannellum eases
pitch, yaw and zoom together, which reads exactly like a map `flyTo`:

.. exec::docs.scenes.flyto_example
    :code: false

.. source::docs/scenes/flyto_example.py
    :defaultExpanded: false
    :withExpandedButton: true

The three triggers in the example, all landing in one callback:

1. **Buttons** — pattern-matching IDs, one per target.
2. **The scene itself** — clicking a ⓘ callback hotspot flies to and zooms
   into that target (`lastClickedHotspot` → `lookAt`).
3. **A simulated external event** — the 🚨 button stands in for any
   server-side trigger (queue message, sensor threshold, websocket push):
   the callback picks the area of interest and dispatches the camera.

.. admonition::Authoring targets
    :icon: mdi:crosshairs-gps
    :color: blue

    Target coordinates are authored the same way as hotspots: turn on
    `showCenterDot=True`, stream `pitch`/`yaw` (and now `hfov`) into a
    readout, aim, copy. The workflow is demonstrated on the
    [Callback Hotspots](/components/hotspots) page.

### When to rebuild vs when to fly

| You want to… | Use | Cost |
|---|---|---|
| Point/zoom the camera | `lookAt` | none — animated in place |
| Jump to another scene | `loadScene` (+ `preloadScenes`) | none — instant if preloaded |
| Move through a world continuously | `panoramaCanvasId` + `dynamicUpdate` | a canvas redraw |
| Change the world's configuration | re-output `tour` | a rebuild — treat it as a real transition |
