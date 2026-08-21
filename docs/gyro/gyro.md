---
name: Gyro Look-Around
description: Steer the 360° camera with the device's gyroscope — orientation props, the iOS permission dance, and a desktop tilt simulator
endpoint: /components/gyro
package: dash_pannellum
icon: mdi:rotate-3d-variant
lastmod: 2026-06-15
---

.. llms_copy::Gyro Look-Around

.. toc::

### What this adds

Hold the phone up and the panorama looks where the phone looks. Gyro
look-around is the most literal form of embodiment the component offers —
no dragging, no joystick: the device *is* the camera. Pannellum ships the
sensor pipeline natively (device-orientation events → quaternion → view);
0.4.0 wires it into the Dash prop system as one request prop and two
truth props:

| Prop | Direction | Meaning |
|------|-----------|---------|
| `orientation` | in (imperative) | Request gyro steering on/off — no rebuild |
| `orientationSupported` | **out** | This browser/device can do it (sensors + mobile browser) |
| `orientationActive` | **out** | The gyro is steering right now |

Request and truth are separate on purpose: the user can deny the iOS
permission prompt, the device may have no sensors, and Pannellum pauses
gyro steering when the user grabs the panorama — `orientationActive` is
the only honest answer.

### Live example

On a phone or tablet, flip the switch and move the device. On a desktop,
the badge will tell you there's no sensor — use the drag pad, which feeds
the camera the same continuous `lookAt` stream a gyroscope would:

.. exec::docs.gyro.gyro_example
    :code: false

.. source::docs/gyro/gyro_example.py
    :defaultExpanded: false
    :withExpandedButton: true

### The platform matrix

| Platform | Behavior |
|----------|----------|
| iOS 13+ (Safari/WebKit) | `startOrientation` triggers the system permission prompt — see the gesture rule below |
| Android (Chrome/Firefox) | Works directly, no prompt |
| Desktop browsers | `orientationSupported` stays `False` — Pannellum gates on a mobile user agent, since desktop "orientation" sensors are noise |
| HTTPS | **Strictly required** — Pannellum checks `location.protocol === "https:"` literally, so plain-HTTP localhost reports unsupported too (use a TLS dev cert or a tunnel to test on a phone) |

.. admonition::The iOS gesture rule
    :icon: mdi:gesture-tap
    :color: yellow

    Safari only shows the motion-sensor permission prompt inside a
    user-gesture window. That's why the example wires the switch through a
    **clientside callback** straight to the `orientation` prop — a server
    round-trip would land outside the gesture and the prompt would be
    silently blocked. Rule of thumb: the write that sets
    `orientation=True` should be the direct result of a tap, with no
    server hop in between.

### How the pieces interact

- **Gyro + drag**: while `orientation` is on, grabbing the panorama pauses
  gyro steering (Pannellum's behavior); `orientationActive` reflects it.
- **Gyro + `lookAt`**: an imperative `lookAt` (a [fly-to](/components/scenes)
  or an [emote](/components/emotes)) competes with the sensor stream —
  turn `orientation` off for directed sequences, back on after. A
  knockdown emote that fights the gyroscope feels broken, not dramatic.
- **Gyro + dynamic canvas**: fully compatible — the sensor steers the
  camera while the [arena](/components/arena) redraws the world under it.
  Phone-in-hand petri dish, no extra code.

### Where this is headed

Gyro turns the camera yaw into a *physical* fact, which makes two future
layers click into place: **spatial audio** (pan sources by the angle
between `yaw` and each contact's bearing — the readouts this page streams
are exactly the inputs an `AudioContext` panner needs) and **world-anchored
zones** (agar hazards that you *hear and face* before you see). The
component-side groundwork for both is already here: `yaw`/`pitch`/`hfov`
out, `orientation` in.
