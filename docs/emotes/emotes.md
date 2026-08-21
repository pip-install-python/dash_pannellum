---
name: Camera Emotes
description: A quick-sheet of directed camera motions — shake, knockdown, lunge — that make the 360° POV feel like a body, not a tripod
endpoint: /components/emotes
package: dash_pannellum
icon: tabler:movie
lastmod: 2026-06-15
---

.. llms_copy::Camera Emotes

.. toc::

### Why direct the camera?

[Fly-to](/components/scenes) points the camera *at things*. Emotes are the
other half of embodiment: they move the camera *as a thing*. A specimen that
takes a hit should **shake**; one that gets slammed should **hit the floor,
lie stunned, and pull itself back up**; a dash forward should **kick the
field of view** the way speed does. Trigger these at the right game moments
and the viewer stops feeling like a tripod in a skybox and starts feeling
like a head that belongs to something.

Technically an emote is nothing new: it's a **keyframe timeline of `lookAt`
writes**, played client-side. No component changes, no server in the loop —
just the imperative camera API sequenced with intent.

### The quick sheet

Look anywhere first — every emote plays **relative to your current gaze**,
then comes to rest (back at your gaze, or re-centered "home" for the
knockdown — a body rights itself):

.. exec::docs.emotes.emotes_example
    :code: false

.. source::docs/emotes/emotes_example.py
    :defaultExpanded: false
    :withExpandedButton: true

| Emote | Game moment | Motion recipe |
|-------|-------------|---------------|
| 🫨 Shake | taking damage | 6 jitters ±3.4°, each ~0.6× the last, 70 ms apiece |
| 🪦 Hit the floor | knockdown / death | pitch −85° in 150 ms → 520 ms stunned hold → rise + re-center over 1.6 s |
| ⚔️ Lunge | attack / dash | hfov punch −36° in 130 ms, brief hold, 650 ms ease back |
| 😵 Dizzy | stun / poison | slow yaw-pitch circle, +8° hfov blur-out, refocus |
| 👀 Scan | spawn / wake | −60° sweep, +120° sweep, settle forward |
| 🤕 Flinch | near miss | pitch +7° & hfov +10° in 90 ms, 480 ms recover |

### The motion-design rules

The sheet (`assets/camera_emotes.js`) encodes a few principles worth
stealing for your own emotes:

1. **In fast, out slow.** Impacts are 90–150 ms; recoveries are 500–1600 ms.
   Reversed, the same keyframes read as floaty nonsense.
2. **Shakes decay.** Constant-amplitude jitter reads as a broken gimbal;
   multiplying amplitude by ~0.6 per cycle reads as absorbed impact.
3. **Speed is field-of-view, not rotation.** A lunge that yaws feels like a
   turn; a lunge that punches `hfov` in and eases it back feels like
   acceleration. (Racing games have abused this forever.)
4. **End at rest.** Every timeline's last frame returns to the base gaze or
   to a deliberate HOME. Never strand the camera mid-emote.
5. **Stay under ~2.5 s.** Longer stops being a reflex and starts being a
   cutscene — which is fine, but then you're back to [fly-to](/components/scenes)
   territory.
6. **One at a time.** The player has a busy-guard; queuing or blending
   emotes is how cameras get motion-sick.

### Anatomy of a keyframe

```js
// assets/camera_emotes.js — knockdown, the "hit the floor & rise" emote
frames(b) {            // b = {pitch, yaw, hfov} at trigger time
    return [
        {pitch: -85, hfov: b.hfov + 14, ms: 150},          // slam DOWN, fast
        {pitch: -85, ms: 60, hold: 520},                   // stunned beat
        {pitch: -22, yaw: HOME.yaw, hfov: b.hfov, ms: 950}, // rise, stage 1
        {pitch: 0,   yaw: HOME.yaw, ms: 700},               // upright, centered
    ];
}
```

Each frame becomes one `set_props(id, {lookAt: {...view, animated: ms}})`,
awaited for `ms + hold`. Omitted axes hold their current value — `lookAt`
semantics — so a frame that only touches `hfov` leaves your gaze alone.

### Triggering from game moments

The example uses buttons, but the trigger is just *any Dash event*. The
pattern mirrors fly-to: pick the emote server-side if the game logic lives
there, or fire it straight from a clientside callback if the moment is
already in the browser (a collision in your game loop, a websocket push):

```python
# server-side game logic decides, client plays it
clientside_callback(
    """async function(hit, pitch, yaw, hfov) {
        if (!hit) { return window.dash_clientside.no_update; }
        const name = hit.fatal ? 'knockdown' : (hit.grazed ? 'flinch' : 'shake');
        return await window.CAM_EMOTES.play('game-pano', name, {pitch, yaw, hfov});
    }""",
    Output("emote-log", "children"),
    Input("hit-store", "data"),          # written by your turn resolver
    State("game-pano", "pitch"), State("game-pano", "yaw"), State("game-pano", "hfov"),
    prevent_initial_call=True,
)
```

Emotes compose with everything else in the package: they're `lookAt`-only,
so they run identically over a static panorama, a tour scene, or a live
[dynamic-canvas arena](/components/arena) — shake the camera *while* the
world redraws under it. A good combo to try: fly-to a contact, then
`lunge` on arrival.

.. admonition::Where this is headed
    :icon: tabler:route
    :color: blue

    The base gaze comes from the component's reported `pitch`/`yaw`/`hfov`
    States (throttled to 4/s) — close enough for reflex moves. If emote
    choreography gets heavier (chained sequences, eased curves, camera
    paths), the package-level answer would be a `playSequence` prop so
    timelines run inside the component against the live viewer state.
    Wishlist material for 0.4.0.
