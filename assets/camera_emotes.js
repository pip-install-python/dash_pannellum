/* camera_emotes — a quick-sheet of directed camera motions for dash-pannellum.
 *
 * An emote is a KEYFRAME TIMELINE of `lookAt` writes, played client-side.
 * Every frame is computed relative to the gaze at trigger time (the base),
 * so the same emote works wherever the user happens to be looking — that's
 * what makes the camera feel HELD by a body instead of bolted to the scene.
 *
 * Motion-design rules baked into the sheet:
 *   - impacts go IN fast and settle OUT slow (knockdown: 150ms down, 1.6s up)
 *   - shakes DECAY (each jitter ~0.6× the last) — constant shake reads fake
 *   - speed is an hfov KICK (lunge: zoom punch in, ease out), not a yaw move
 *   - emotes END at rest — either back at the base or at HOME ("the body
 *     rights itself"); never leave the camera somewhere weird
 *   - keep it under ~2.5s; longer stops feeling like a reflex
 *
 * No component changes needed: this is pure 0.2.0/0.3.0 imperative API.
 */
/* eslint-disable no-magic-numbers */
(function () {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    // Where "rising back up" re-centers to — the scene's forward direction.
    const HOME = {yaw: 5, pitch: 0};

    let busy = false;

    function look(targetId, view, ms) {
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props(targetId, {
                lookAt: {...view, animated: ms},
            });
        }
    }

    /* Each emote: label/hint for the UI + frames(base) → keyframes.
     * A keyframe: {pitch?, yaw?, hfov?, ms, hold?} — omitted axes HOLD their
     * current value (lookAt semantics), `ms` is the eased move duration,
     * `hold` lingers before the next frame (the "lie there stunned" beat). */
    const SHEET = {
        shake: {
            label: '🫨 Shake',
            hint: 'impact / taking damage — decaying jitter around the gaze',
            frames(b) {
                const frames = [];
                let amp = 3.4;
                for (let i = 0; i < 6; i++) {
                    frames.push({
                        yaw: b.yaw + (i % 2 ? amp : -amp),
                        pitch: b.pitch + (i % 2 ? -amp * 0.5 : amp * 0.4),
                        ms: 70,
                    });
                    amp *= 0.62;
                }
                frames.push({yaw: b.yaw, pitch: b.pitch, ms: 140});
                return frames;
            },
        },
        knockdown: {
            label: '🪦 Hit the floor',
            hint: 'slammed down, a stunned beat, then rise and re-center',
            frames(b) {
                return [
                    // DOWN: fast — you don't ease into the floor
                    {pitch: -85, hfov: Math.min(b.hfov + 14, 115), ms: 150},
                    // stunned beat, face in the agar
                    {pitch: -85, ms: 60, hold: 520},
                    // UP: slow, two stages, ending centered on HOME
                    {pitch: -22, yaw: HOME.yaw, hfov: b.hfov, ms: 950},
                    {pitch: HOME.pitch, yaw: HOME.yaw, ms: 700},
                ];
            },
        },
        lunge: {
            label: '⚔️ Lunge',
            hint: 'attack dash — an hfov punch reads as speed, not a turn',
            frames(b) {
                return [
                    {hfov: Math.max(b.hfov - 36, 48), pitch: b.pitch - 5, ms: 130},
                    {hfov: Math.max(b.hfov - 36, 48), ms: 40, hold: 90},
                    {hfov: b.hfov, pitch: b.pitch, ms: 650},
                ];
            },
        },
        dizzy: {
            label: '😵 Dizzy',
            hint: 'stunned / poisoned — a slow drunken circle, then refocus',
            frames(b) {
                return [
                    {yaw: b.yaw + 18, pitch: b.pitch + 6, ms: 330},
                    {yaw: b.yaw + 36, pitch: b.pitch, ms: 330},
                    {yaw: b.yaw + 18, pitch: b.pitch - 6, ms: 330},
                    {yaw: b.yaw, pitch: b.pitch, hfov: b.hfov + 8, ms: 330},
                    {hfov: b.hfov, ms: 380},
                ];
            },
        },
        scan: {
            label: '👀 Scan',
            hint: 'waking / spawning — sweep the surroundings, settle forward',
            frames(b) {
                return [
                    {yaw: b.yaw - 60, pitch: b.pitch + 3, ms: 520},
                    {yaw: b.yaw + 60, ms: 950},
                    {yaw: HOME.yaw, pitch: HOME.pitch, ms: 620},
                ];
            },
        },
        flinch: {
            label: '🤕 Flinch',
            hint: 'a near miss — recoil up and out, recover quickly',
            frames(b) {
                return [
                    {pitch: b.pitch + 7, hfov: Math.min(b.hfov + 10, 115), ms: 90},
                    {pitch: b.pitch, hfov: b.hfov, ms: 480},
                ];
            },
        },
    };

    window.CAM_EMOTES = {
        SHEET,

        /* Play one emote on a DashPannellum. `base` is {pitch, yaw, hfov}
         * from the component's reported props (4/s throttle — close enough
         * for a reflex move). Returns the status line for the UI. */
        async play(targetId, name, base) {
            const emote = SHEET[name];
            if (!emote) {
                return '';
            }
            if (busy) {
                return '⏳ an emote is already playing — let the body finish';
            }
            busy = true;
            try {
                const b = {
                    pitch: typeof base.pitch === 'number' ? base.pitch : HOME.pitch,
                    yaw: typeof base.yaw === 'number' ? base.yaw : HOME.yaw,
                    hfov: typeof base.hfov === 'number' ? base.hfov : 95,
                };
                for (const frame of emote.frames(b)) {
                    const {ms, hold, ...view} = frame;
                    look(targetId, view, ms);
                    /* eslint-disable-next-line no-await-in-loop */
                    await sleep(ms + (hold || 0) + 30);
                }
            } finally {
                busy = false;
            }
            return `${emote.label} — ${emote.hint}`;
        },
    };
})();
