---
name: API Reference
description: Every DashPannellum prop — configuration, behavior and read-only state
endpoint: /api
package: dash_pannellum
icon: mdi:api
---

.. llms_copy::API Reference

.. toc::

### Component props

The table below is generated from the component's own metadata, so it always matches the installed version.

.. kwargs::dash_pannellum.DashPannellum

---

### Read-only props

These update from the viewer — use them as callback `Input`s, never set them yourself:

| Prop | Updates when |
|------|--------------|
| `loaded` | The panorama or video finishes loading |
| `pitch` | The camera pitch changes (throttled, change-detected) |
| `yaw` | The camera yaw changes (throttled, change-detected) |
| `hfov` | The zoom changes (throttled, change-detected) — new in 0.2.0 |
| `currentScene` | The active tour scene changes |
| `lastClickedHotspot` | A callback hotspot is clicked |
| `orientationSupported` | Gyro steering is possible here (mobile + HTTPS) — new in 0.4.0 |
| `orientationActive` | The gyroscope is steering right now — new in 0.4.0 |

### Imperative props (0.2.0 / 0.3.0)

These act on the live viewer **without a rebuild** — output them from
callbacks (or `window.dash_clientside.set_props` for high-frequency use):

| Prop | Action |
|------|--------|
| `lookAt` | `{pitch, yaw, hfov, animated}` — pan/zoom the camera; omitted fields hold |
| `loadScene` | Scene ID string — switch tour scenes |
| `callbackHotspots` | **Live**: per-name diff — position-only changes move the existing DOM node in place (0.3.1), other changes recreate just that hotspot |
| `dynamicUpdate` | Re-upload the texture each frame — pairs with the `panoramaCanvasId` scene key (0.3.0) for canvas-backed worlds |
| `orientation` | Request gyro look-around (0.4.0) — set from a clientside callback on a tap for the iOS permission prompt |

See [Scene Configuration](/components/scenes) for the fly-to pattern, the
[Joystick Arena](/components/arena) for the full movement stack, and
[Gyro Look-Around](/components/gyro) for device-orientation steering.

---

### Changes since 0.0.6

.. admonition::Breaking changes in 0.1.0
    :icon: mdi:alert-outline
    :color: yellow

    - **Dash 4.2+ required** (was Dash 1/2 era). The package now ships `pyproject.toml` packaging and a React 18 build.
    - **`customControls` is now coherent across modes**: `True` hides the built-in zoom/fullscreen controls (previously it was ignored for image panoramas and inverted for video).
    - **Video no longer autoplays**; users press play. Set up your own interaction if you need autoplay (browsers block autoplay-with-audio anyway).
    - **`pitch`/`yaw` updates are throttled to 4/s and change-detected** (previously 10/s unconditionally), so idle viewers no longer trigger callbacks.

New in 0.1.0: configuration props are **live** — output a new `tour` (or `multiRes`/`video`) from a callback and the viewer re-initializes with it, so panoramas can be swapped dynamically. Callback hotspots use real Pannellum click handlers (they previously relied on a viewer event that never fired reliably), script loading is deduplicated so several viewers can share one page, and the `loaded` prop is properly declared.
