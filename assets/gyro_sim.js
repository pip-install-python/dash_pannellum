/* gyro_sim — a desktop stand-in for gyro look-around.
 *
 * Pannellum (correctly) refuses device-orientation on non-mobile browsers,
 * so the docs page offers this drag-pad instead: dragging maps to the same
 * continuous lookAt writes a phone's gyroscope produces. Same camera feel,
 * different sensor. Document-level delegation so it survives Dash's
 * dynamic page mounts.
 */
/* eslint-disable no-magic-numbers */
(function () {
    const TARGET = 'gyro-pano';
    const state = {dragging: false, lastX: 0, lastY: 0, yaw: 5, pitch: 0};

    const pad = (e) =>
        e.target && e.target.closest ? e.target.closest('#gyro-pad') : null;

    function moveDot(padEl, clientX, clientY) {
        const dot = document.getElementById('gyro-pad-dot');
        if (!dot || !padEl) {
            return;
        }
        const r = padEl.getBoundingClientRect();
        const x = Math.max(8, Math.min(r.width - 8, clientX - r.left));
        const y = Math.max(8, Math.min(r.height - 8, clientY - r.top));
        dot.style.left = `${x}px`;
        dot.style.top = `${y}px`;
    }

    document.addEventListener('pointerdown', (e) => {
        const el = pad(e);
        if (!el) {
            return;
        }
        state.dragging = true;
        state.lastX = e.clientX;
        state.lastY = e.clientY;
        moveDot(el, e.clientX, e.clientY);
        e.preventDefault();
    });

    document.addEventListener('pointermove', (e) => {
        if (!state.dragging) {
            return;
        }
        const dx = e.clientX - state.lastX;
        const dy = e.clientY - state.lastY;
        state.lastX = e.clientX;
        state.lastY = e.clientY;
        state.yaw += dx * 0.45;
        state.pitch = Math.max(-60, Math.min(60, state.pitch - dy * 0.35));
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props(TARGET, {
                lookAt: {yaw: state.yaw, pitch: state.pitch, animated: 90},
            });
        }
        moveDot(document.getElementById('gyro-pad'), e.clientX, e.clientY);
    });

    document.addEventListener('pointerup', () => {
        state.dragging = false;
    });
})();
