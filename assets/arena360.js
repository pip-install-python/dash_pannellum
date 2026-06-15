/* arena360 — compose an equirectangular 360° panorama from a petri-dish
 * floor TILESET, entirely client-side, and drive dash-pannellum with it.
 *
 * The floor is an N×N block of native-zoom slippy tiles (the same
 * pip-install-python petri tilesets dash-leaflet2 serves flat). Standing at
 * eye height above that floor, every output pixel below the horizon is a ray
 * that hits the floor plane at ground distance g = EYE_H / tan(-pitch) along
 * bearing yaw — sample the tile mosaic there. Above the horizon: dark
 * condenser "sky". The result goes to dash-pannellum as a data-URI panorama
 * (no HTTP round-trip), rebuilt only when the player MOVES; looking around
 * is free (drag, or the joystick writing the 0.2.0 `lookAt` prop).
 *
 * Bearing contract matches the game's placement.js: yaw 0° = north = "up"
 * on the flat map, clockwise. world x = east, y = south.
 */
/* eslint-disable no-magic-numbers */
(function () {
    const TILE_URL = (z, x, y) => `/assets/tilesets/dish/${z}/${x}/${y}.jpg`;

    const ARENAS = {
        early: {z: 15, x0: 16383, y0: 16383, n: 3, label: 'Early 3×3 @ z15'},
        mid: {z: 9, x0: 254, y0: 254, n: 5, label: 'Mid 5×5 @ z9'},
        late: {z: 3, x0: 1, y0: 1, n: 7, label: 'Late 7×7 @ z3'},
    };

    // World model: the mosaic spans SPAN wu; you stand EYE wu above it.
    const SPAN = 1024;          // mosaic edge in world units
    const EYE = 14;             // eye height (wu) — petri-specimen scale
    const FAR = SPAN * 0.62;    // ground distance where fog wins
    const CLAMP = SPAN * 0.34;  // soft wall for the player
    const STEP = SPAN * 0.055;  // one glide step
    const STEP_MS = 420;        // glide cadence while the stick is pushed
    const PANO_W = 1792;
    const PANO_H = 896;

    // sky / fog palette (dark condenser field over glowing agar)
    const SKY_TOP = [4, 8, 16];
    const SKY_HORIZON = [24, 44, 64];
    const FOG = [16, 32, 48];

    const CANVAS_ID = 'arena360-canvas';

    const S = {
        arena: 'early',
        px: 0,
        py: 0,
        gazeYaw: 0,
        glideBearing: 0,
        glideTimer: null,
        building: false,
        bound: false,       // tour handed to dash-pannellum yet?
        mosaics: {},        // arena key -> {data, w, h} ImageData cache
        panoCanvas: null,
    };

    /* The persistent texture canvas. dash-pannellum binds the scene to it
     * (panoramaCanvasId + dynamicUpdate) — after that, movement is just
     * redrawing these pixels. No tour re-outputs, no rebuild, no flash. */
    function textureCanvas() {
        if (!S.panoCanvas) {
            const el = document.createElement('canvas');
            el.id = CANVAS_ID;
            el.width = PANO_W;
            el.height = PANO_H;
            el.style.display = 'none';
            document.body.appendChild(el);
            S.panoCanvas = el;
        }
        return S.panoCanvas;
    }

    function loadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });
    }

    async function mosaic(arenaKey) {
        if (S.mosaics[arenaKey]) {
            return S.mosaics[arenaKey];
        }
        const a = ARENAS[arenaKey];
        const tilePx = Math.min(512, Math.floor(2560 / a.n));
        const size = tilePx * a.n;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d', {willReadFrequently: true});
        const jobs = [];
        for (let i = 0; i < a.n; i++) {
            for (let j = 0; j < a.n; j++) {
                jobs.push(
                    loadImage(TILE_URL(a.z, a.x0 + i, a.y0 + j)).then((img) =>
                        ctx.drawImage(img, i * tilePx, j * tilePx, tilePx, tilePx)
                    )
                );
            }
        }
        await Promise.all(jobs);
        const data = ctx.getImageData(0, 0, size, size);
        S.mosaics[arenaKey] = {data: data.data, w: size, h: size};
        return S.mosaics[arenaKey];
    }

    /* Compose the equirect panorama for the current position, straight into
     * the texture canvas. ~60ms; the sphere picks it up on the next frame. */
    async function compose() {
        const m = await mosaic(S.arena);
        const ctx = textureCanvas().getContext('2d', {willReadFrequently: true});
        const out = ctx.createImageData(PANO_W, PANO_H);
        const px = out.data;
        const half = PANO_H / 2;
        const mscale = m.w / SPAN;

        for (let row = 0; row < PANO_H; row++) {
            const pitch = (0.5 - row / PANO_H) * Math.PI; // +90° .. −90°
            if (pitch >= 0) {
                // sky: vertical gradient toward a glowing horizon band
                const t = 1 - pitch / (Math.PI / 2); // 0 zenith → 1 horizon
                const g = t * t;
                const r0 = SKY_TOP[0] + (SKY_HORIZON[0] - SKY_TOP[0]) * g;
                const g0 = SKY_TOP[1] + (SKY_HORIZON[1] - SKY_TOP[1]) * g;
                const b0 = SKY_TOP[2] + (SKY_HORIZON[2] - SKY_TOP[2]) * g;
                for (let col = 0; col < PANO_W; col++) {
                    const o = (row * PANO_W + col) * 4;
                    px[o] = r0;
                    px[o + 1] = g0;
                    px[o + 2] = b0;
                    px[o + 3] = 255;
                }
                continue;
            }
            const ground = EYE / Math.tan(-pitch);
            const fog = Math.min(1, ground / FAR);
            const keep = 1 - fog;
            for (let col = 0; col < PANO_W; col++) {
                const yawRad = ((col / PANO_W) * 360 - 180) * (Math.PI / 180);
                // yaw 0 = north = −y on the flat map, clockwise
                const wx = S.px + ground * Math.sin(yawRad);
                const wy = S.py - ground * Math.cos(yawRad);
                const u = Math.floor((wx / SPAN + 0.5) * mscale * SPAN);
                const v = Math.floor((wy / SPAN + 0.5) * mscale * SPAN);
                const o = (row * PANO_W + col) * 4;
                if (u >= 0 && u < m.w && v >= 0 && v < m.h) {
                    const s = (v * m.w + u) * 4;
                    px[o] = m.data[s] * keep + FOG[0] * fog;
                    px[o + 1] = m.data[s + 1] * keep + FOG[1] * fog;
                    px[o + 2] = m.data[s + 2] * keep + FOG[2] * fog;
                } else {
                    px[o] = FOG[0];
                    px[o + 1] = FOG[1];
                    px[o + 2] = FOG[2];
                }
                px[o + 3] = 255;
            }
        }
        ctx.putImageData(out, 0, 0);
    }

    function tourFor(yaw) {
        return {
            default: {firstScene: 'arena'},
            scenes: {
                arena: {
                    type: 'equirectangular',
                    panoramaCanvasId: CANVAS_ID,   // dynamic canvas scene (0.3.0)
                    hfov: 95,
                    minHfov: 55,
                    maxHfov: 115,
                    yaw,
                    pitch: -10,
                },
            },
        };
    }

    /* A soft dip-to-dark over the viewer, used only for arena SWITCHES —
     * glide steps are continuous and need no transition at all. */
    function fadePulse() {
        const wrap = document.getElementById('arena-pano');
        if (!wrap) {
            return;
        }
        wrap.style.transition = 'opacity 140ms ease-in-out';
        wrap.style.opacity = '0.15';
        setTimeout(() => {
            wrap.style.opacity = '1';
        }, 160);
    }

    function setProps(props) {
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props('arena-pano', props);
        }
    }

    function hud() {
        return (
            `${ARENAS[S.arena].label}  ·  pos ${S.px.toFixed(0)}, ` +
            `${S.py.toFixed(0)} wu  ·  gaze ${((S.gazeYaw % 360) + 360) % 360 | 0}°`
        );
    }

    /* Keep the HUD live from the glide loop (between joystick events React
     * isn't re-rendering it; the next drive() return overwrites cleanly). */
    function pushHud() {
        const el = document.getElementById('arena-hud');
        if (el) {
            el.textContent = hud();
        }
    }

    /* Redraw the texture for the current position. The ONE-TIME tour bind
     * happens on the first call; after that the viewer is never rebuilt —
     * dynamicUpdate keeps the sphere reading the canvas every frame. */
    async function redraw() {
        if (S.building) {
            return hud();
        }
        S.building = true;
        try {
            await compose();
            if (!S.bound) {
                S.bound = true;
                setProps({tour: tourFor(S.gazeYaw)});
            }
        } finally {
            S.building = false;
        }
        return hud();
    }

    window.ARENA360 = {
        ARENAS,

        /* First paint and arena switches. */
        async start(arenaKey) {
            this._stopGlide();
            if (arenaKey && ARENAS[arenaKey]) {
                if (S.bound && arenaKey !== S.arena) {
                    fadePulse();
                }
                S.arena = arenaKey;
            }
            S.px = 0;
            S.py = 0;
            return redraw();
        },

        /* rc-joystick angle → compass bearing (0° = north/up, clockwise).
         * rc-joystick reports math-convention angles — 0° at screen-right
         * growing COUNTER-clockwise (up = 90°) — verified empirically. */
        _a2b(angle) {
            return (((90 - angle) % 360) + 360) % 360;
        },

        _step() {
            const rad = S.glideBearing * (Math.PI / 180);
            S.px = Math.max(-CLAMP, Math.min(CLAMP, S.px + STEP * Math.sin(rad)));
            S.py = Math.max(-CLAMP, Math.min(CLAMP, S.py - STEP * Math.cos(rad)));
            redraw().then(pushHud);   // pixels only — the viewer never rebuilds
        },

        _stopGlide() {
            if (S.glideTimer) {
                clearInterval(S.glideTimer);
                S.glideTimer = null;
            }
        },

        /* Joystick frame: tilt = look (lookAt — no rebuild), pin to the rim
         * = glide. rc-joystick only emits on CHANGE, so a held stick goes
         * silent — the glide runs on an internal cadence until the stick
         * drops below the rim or is released. */
        async drive(rawAngle, distance) {
            if (rawAngle == null || !distance) {
                this._stopGlide();
                return hud();
            }
            const angle = this._a2b(rawAngle);
            S.gazeYaw = angle;
            S.glideBearing = angle;
            setProps({lookAt: {yaw: angle, animated: 220}});
            // rc-joystick's `distance` is RAW PIXELS from center (capped at
            // baseRadius — 70 in the example), not the 0–1 of its docs.
            // Verified by probing; glide only when pinned near the rim.
            if (distance >= 62) {
                if (!S.glideTimer) {
                    this._step();
                    S.glideTimer = setInterval(() => this._step(), STEP_MS);
                }
            } else {
                this._stopGlide();
            }
            return hud();
        },
    };
})();
