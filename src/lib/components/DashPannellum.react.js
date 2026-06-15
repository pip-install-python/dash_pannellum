import React, {useEffect, useRef} from 'react';
import PropTypes from 'prop-types';
import {initializePlugin} from '../index';

const PANNELLUM_CSS = 'https://cdn.pannellum.org/2.5/pannellum.css';
const PANNELLUM_JS = 'https://cdn.pannellum.org/2.5/pannellum.js';
const VIDEOJS_CSS = 'https://vjs.zencdn.net/7.20.3/video-js.min.css';
const VIDEOJS_JS = 'https://vjs.zencdn.net/7.20.3/video.min.js';
const VHS_JS =
    'https://unpkg.com/@videojs/http-streaming@2.14.2/dist/videojs-http-streaming.min.js';

const VIEW_POLL_MS = 250;

/* Hotspot diff helpers (live callbackHotspots updates). */
const sameSpot = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/* True when only pitch/yaw differ — the case we can apply IN PLACE. */
const positionOnlyChange = (a, b) => {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const key of keys) {
        if (key === 'pitch' || key === 'yaw') {
            continue;
        }
        if (JSON.stringify(a[key]) !== JSON.stringify(b[key])) {
            return false;
        }
    }
    return true;
};

const SPINNER_CSS_ID = 'dash-pannellum-spinner-css';

/**
 * Inject (once) the component's base stylesheet:
 * - hideLoadingSpinner support (suppress Pannellum's "Loading..." box);
 * - a transparent viewer container. Pannellum's default is #f4f4f4, which
 *   reads as a white flash during any rebuild on dark UIs — transparent
 *   lets the host page's background show instead.
 */
const ensureSpinnerCss = () => {
    if (document.getElementById(SPINNER_CSS_ID)) {
        return;
    }
    const style = document.createElement('style');
    style.id = SPINNER_CSS_ID;
    style.textContent =
        '.dash-pannellum-no-spinner .pnlm-load-box{display:none !important;}' +
        '.dash-pannellum .pnlm-container{background:transparent !important;}';
    document.head.appendChild(style);
};

/**
 * Append a stylesheet once; resolves immediately if it is already present.
 */
const ensureStylesheet = (href) =>
    new Promise((resolve, reject) => {
        const existing = document.querySelector(`link[href="${href}"]`);
        if (existing) {
            resolve();
            return;
        }
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.onload = resolve;
        link.onerror = reject;
        document.head.appendChild(link);
    });

/**
 * Append a script once. Multiple viewers on the same page share the tag:
 * later callers poll `isReady` (a window-global check) instead of injecting
 * a duplicate script element.
 */
const ensureScript = (src, isReady) =>
    new Promise((resolve, reject) => {
        if (isReady && isReady()) {
            resolve();
            return;
        }
        let script = document.querySelector(`script[src="${src}"]`);
        if (!script) {
            script = document.createElement('script');
            script.src = src;
            script.async = true;
            script.onerror = reject;
            document.body.appendChild(script);
        }
        const poll = setInterval(() => {
            if (!isReady || isReady()) {
                clearInterval(poll);
                resolve();
            }
        }, 50);
        script.addEventListener('load', () => {
            if (!isReady || isReady()) {
                clearInterval(poll);
                resolve();
            }
        });
    });

/**
 * DashPannellum wraps the Pannellum WebGL panorama viewer for Dash.
 * It supports equirectangular panoramas, guided tours with hotspots,
 * multi-resolution tiled panoramas and 360° video (via video.js).
 */
const DashPannellum = ({
    id,
    width = '600px',
    height = '400px',
    tour = null,
    multiRes = null,
    video = null,
    customControls = false,
    showCenterDot = false,
    autoLoad = true,
    compass = false,
    northOffset = 0,
    useHttpStreaming = false,
    callbackHotspots = {},
    lookAt = null,
    loadScene = null,
    hideLoadingSpinner = false,
    preloadScenes = true,
    dynamicUpdate = false,
    orientation = false,
    setProps,
}) => {
    const viewerRef = useRef(null);
    const playerRef = useRef(null);
    const intervalRef = useRef(null);
    const lastViewRef = useRef({});
    // Names of the callback hotspots currently applied, keyed by scene id,
    // plus a signature so the live-update effect can no-op on equal props.
    const appliedSpotsRef = useRef({signature: null, byScene: {}});
    // Latest callbackHotspots prop — the 'load' handler reads this instead of
    // its closure so a scene change can't resurrect stale hotspots.
    const latestSpotsRef = useRef(callbackHotspots);
    latestSpotsRef.current = callbackHotspots;
    // Same latest-value pattern for the gyro request, applied on 'load'.
    const latestOrientationRef = useRef(orientation);
    latestOrientationRef.current = orientation;

    const reportView = () => {
        const viewer = playerRef.current;
        if (!viewer || !setProps) {
            return;
        }
        const view = {
            pitch: Math.round(viewer.getPitch() * 100) / 100,
            yaw: Math.round(viewer.getYaw() * 100) / 100,
            hfov: Math.round(viewer.getHfov() * 100) / 100,
            currentScene: viewer.getScene(),
            orientationSupported: false,
            orientationActive: false,
        };
        try {
            view.orientationSupported = Boolean(viewer.isOrientationSupported());
            view.orientationActive = Boolean(viewer.isOrientationActive());
        } catch (e) {
            /* older pannellum builds — leave both false */
        }
        const last = lastViewRef.current;
        if (
            view.pitch !== last.pitch ||
            view.yaw !== last.yaw ||
            view.hfov !== last.hfov ||
            view.currentScene !== last.currentScene ||
            view.orientationSupported !== last.orientationSupported ||
            view.orientationActive !== last.orientationActive
        ) {
            lastViewRef.current = view;
            setProps(view);
        }
    };

    /**
     * Request or release gyro look-around. Pannellum gates this on its own
     * support detection (DeviceOrientationEvent + a mobile user agent) and
     * runs the iOS 13+ permission prompt inside startOrientation — so on
     * iOS the enabling prop write should originate from a clientside
     * callback on a direct user tap, to stay in the gesture window.
     * Outcomes are reported through orientationSupported/orientationActive.
     */
    const applyOrientation = (want) => {
        const viewer = playerRef.current;
        if (!viewer || video) {
            return;
        }
        try {
            if (want) {
                viewer.startOrientation();
            } else {
                viewer.stopOrientation();
            }
        } catch (e) {
            /* unsupported — orientationSupported stays false */
        }
    };

    /**
     * Sync the viewer's callback hotspots with the prop value — a per-name
     * diff, not a wholesale replace:
     * - unchanged hotspots are left alone (DOM node, hover state intact);
     * - position-only changes are applied IN PLACE by mutating the spec
     *   object Pannellum holds — it re-reads pitch/yaw every render, so the
     *   existing DOM node simply moves (this is what lets contacts drift);
     * - any other change (text, type, cssClass, …) removes + re-adds;
     * - vanished names are removed.
     * Each hotspot gets id = name so it can be addressed across updates.
     */
    const syncCallbackHotspots = (spots) => {
        const viewer = playerRef.current;
        if (!viewer || video) {
            return;
        }
        // Never touch hotspots before the panorama is loaded: a pre-load
        // addHotSpot gets a SECOND div from Pannellum's own load pass,
        // leaving an orphan marker. The on('load') sync reads the latest
        // prop value, so dropped early updates are applied then.
        try {
            if (!viewer.isLoaded()) {
                return;
            }
        } catch (e) {
            return;
        }
        const signature = JSON.stringify(spots || {});
        if (signature === appliedSpotsRef.current.signature) {
            return;
        }
        const prevByScene = appliedSpotsRef.current.byScene || {};
        const nextByScene = {};
        let movedInPlace = 0;

        const sceneIds = new Set([
            ...Object.keys(prevByScene),
            ...Object.keys(spots || {}),
        ]);

        sceneIds.forEach((sceneId) => {
            const prevEntries = prevByScene[sceneId] || {};
            const nextList = (spots || {})[sceneId] || [];
            const nextNames = new Set(nextList.map((h) => h.name));

            Object.keys(prevEntries).forEach((name) => {
                if (!nextNames.has(name)) {
                    try {
                        viewer.removeHotSpot(name, sceneId);
                    } catch (e) {
                        /* scene may be gone — nothing to remove */
                    }
                }
            });

            const kept = {};
            nextList.forEach((hotspot) => {
                const prev = prevEntries[hotspot.name];
                if (prev) {
                    if (sameSpot(prev.source, hotspot)) {
                        kept[hotspot.name] = prev;
                        return;
                    }
                    if (positionOnlyChange(prev.source, hotspot)) {
                        prev.spec.pitch = hotspot.pitch;
                        prev.spec.yaw = hotspot.yaw;
                        prev.source = hotspot;
                        kept[hotspot.name] = prev;
                        movedInPlace += 1;
                        return;
                    }
                    try {
                        viewer.removeHotSpot(hotspot.name, sceneId);
                    } catch (e) {
                        /* fall through to re-add */
                    }
                }
                const spec = {
                    ...hotspot,
                    id: hotspot.name,
                    type:
                        hotspot.type === 'callbackhotspot'
                            ? 'info'
                            : hotspot.type,
                    clickHandlerFunc: () => {
                        if (setProps) {
                            setProps({lastClickedHotspot: hotspot.name});
                        }
                    },
                };
                try {
                    viewer.addHotSpot(spec, sceneId);
                    kept[hotspot.name] = {source: hotspot, spec};
                } catch (e) {
                    /* eslint-disable-next-line no-console */
                    console.warn('DashPannellum: addHotSpot failed', e);
                }
            });
            if (Object.keys(kept).length) {
                nextByScene[sceneId] = kept;
            }
        });

        // In-place moves need one render to show on an idle viewer.
        // setUpdate kicks Pannellum's animate loop even when re-asserting
        // the current value (a same-value setPitch short-circuits instead),
        // so this renders once on idle viewers and is a no-op state-wise
        // on continuously-updating ones.
        if (movedInPlace > 0) {
            try {
                viewer.setUpdate(Boolean(dynamicUpdate));
            } catch (e) {
                /* viewer mid-boot — next render shows the moves */
            }
        }

        appliedSpotsRef.current = {signature, byScene: nextByScene};
    };

    const initializeVideo = () => {
        const videojs = window.videojs;
        if (!videojs) {
            return;
        }
        const playerOptions = {
            controls: true,
            autoplay: false,
            preload: autoLoad ? 'auto' : 'metadata',
            width: '100%',
            height: '100%',
            sources: video.sources,
        };
        if (useHttpStreaming) {
            playerOptions.html5 = {vhs: {overrideNative: true}};
        }

        playerRef.current = videojs(viewerRef.current, playerOptions);
        playerRef.current.ready(() => {
            playerRef.current.pannellum({
                autoLoad,
                showControls: !customControls,
                compass,
                northOffset,
            });
            if (setProps) {
                setProps({loaded: true});
            }
        });
    };

    const initializePanorama = () => {
        let config;
        if (multiRes) {
            config = {
                type: 'multires',
                multiRes,
                autoLoad,
                compass,
                northOffset,
                showControls: !customControls,
            };
        } else if (tour) {
            config = {
                ...tour,
                autoLoad,
                compass,
                northOffset,
                showControls: !customControls,
            };
            // Dynamic canvas scenes: a scene may name a <canvas> element via
            // `panoramaCanvasId` instead of a panorama URL. The canvas becomes
            // the texture source (Pannellum's dynamic mode) — redraw the
            // canvas and the sphere updates in place with no rebuild and no
            // camera reset. Pair with the `dynamicUpdate` prop.
            if (config.scenes) {
                const scenes = {};
                Object.entries(config.scenes).forEach(([sceneId, scene]) => {
                    if (scene && scene.panoramaCanvasId) {
                        const el = document.getElementById(scene.panoramaCanvasId);
                        if (el) {
                            const {panoramaCanvasId, ...rest} = scene;
                            scenes[sceneId] = {
                                ...rest,
                                panorama: el,
                                dynamic: true,
                            };
                            return;
                        }
                        /* eslint-disable-next-line no-console */
                        console.warn(
                            `DashPannellum: canvas #${scene.panoramaCanvasId} ` +
                                'not found for scene ' + sceneId
                        );
                    }
                    scenes[sceneId] = scene;
                });
                config = {...config, scenes};
            }
        }

        if (!config) {
            return;
        }
        if (playerRef.current) {
            playerRef.current.destroy();
        }
        appliedSpotsRef.current = {signature: null, byScene: {}};
        playerRef.current = window.pannellum.viewer(viewerRef.current, config);

        // Callback hotspots are applied through the imperative API (not baked
        // into the config) so later prop updates can diff them without a
        // viewer rebuild. Synced on 'load' — idempotent via the signature, and
        // reading the latest prop value so a stale closure can't downgrade.
        playerRef.current.on('load', () => {
            if (setProps) {
                setProps({loaded: true});
            }
            syncCallbackHotspots(latestSpotsRef.current);
            if (latestOrientationRef.current) {
                applyOrientation(true);
            }
        });
        if (setProps) {
            setProps({loaded: autoLoad});
        }

        // Warm the browser cache for the other scenes' panoramas so tour
        // jumps (hotspots or the loadScene prop) don't show a loading box.
        if (preloadScenes && config.scenes) {
            const first = (config.default || {}).firstScene;
            Object.entries(config.scenes).forEach(([sceneId, scene]) => {
                const src = scene && scene.panorama;
                if (
                    sceneId !== first &&
                    typeof src === 'string' &&
                    !src.startsWith('data:')
                ) {
                    new Image().src = src;
                }
            });
        }

        if (dynamicUpdate) {
            try {
                playerRef.current.setUpdate(true);
            } catch (e) {
                /* applied again by the dynamicUpdate effect */
            }
        }

        intervalRef.current = setInterval(reportView, VIEW_POLL_MS);
    };

    // Re-initializes whenever a configuration prop changes, so panoramas can
    // be swapped from Dash callbacks. The cancelled flag keeps a torn-down
    // effect's async boot from racing the replacement viewer.
    useEffect(() => {
        let cancelled = false;
        ensureSpinnerCss();
        const boot = async () => {
            try {
                await ensureStylesheet(PANNELLUM_CSS);
                await ensureScript(PANNELLUM_JS, () => window.pannellum);

                if (video) {
                    await ensureStylesheet(VIDEOJS_CSS);
                    await ensureScript(VIDEOJS_JS, () => window.videojs);
                    if (useHttpStreaming) {
                        await ensureScript(VHS_JS, () => window.videojs);
                    }
                    if (cancelled) {
                        return;
                    }
                    initializePlugin();
                    initializeVideo();
                } else {
                    if (cancelled) {
                        return;
                    }
                    initializePanorama();
                }
            } catch (error) {
                /* eslint-disable-next-line no-console */
                console.error('DashPannellum: failed to load viewer assets', error);
            }
        };
        boot();

        return () => {
            cancelled = true;
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
            if (playerRef.current) {
                if (video) {
                    playerRef.current.dispose();
                } else {
                    playerRef.current.destroy();
                }
                playerRef.current = null;
            }
        };
    }, [tour, multiRes, video, autoLoad, compass, northOffset, useHttpStreaming]);

    // Imperative camera write — no rebuild. Outputting a new lookAt object
    // from a callback (or window.dash_clientside.set_props) pans/zooms the
    // existing viewer. Missing fields keep their current value.
    useEffect(() => {
        const viewer = playerRef.current;
        if (!viewer || video || !lookAt) {
            return;
        }
        try {
            viewer.lookAt(
                typeof lookAt.pitch === 'number' ? lookAt.pitch : viewer.getPitch(),
                typeof lookAt.yaw === 'number' ? lookAt.yaw : viewer.getYaw(),
                typeof lookAt.hfov === 'number' ? lookAt.hfov : viewer.getHfov(),
                typeof lookAt.animated === 'number' ? lookAt.animated : 1000
            );
        } catch (e) {
            /* viewer still booting — the scene config carries initial view */
        }
    }, [lookAt, video]);

    // Imperative scene switch — no rebuild. Guarded so reflected state can't
    // loop, and ignored for unknown scene ids.
    useEffect(() => {
        const viewer = playerRef.current;
        if (!viewer || video || !loadScene) {
            return;
        }
        try {
            const scenes = (viewer.getConfig() || {}).scenes || {};
            if (loadScene !== viewer.getScene() && scenes[loadScene]) {
                viewer.loadScene(loadScene);
            }
        } catch (e) {
            /* viewer still booting — firstScene applies */
        }
    }, [loadScene, video]);

    // Live hotspot updates — diffed through addHotSpot/removeHotSpot.
    useEffect(() => {
        syncCallbackHotspots(callbackHotspots);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [callbackHotspots]);

    // Continuous texture refresh for dynamic (canvas) panoramas.
    useEffect(() => {
        const viewer = playerRef.current;
        if (!viewer || video) {
            return;
        }
        try {
            viewer.setUpdate(Boolean(dynamicUpdate));
        } catch (e) {
            /* viewer still booting — applied at init */
        }
    }, [dynamicUpdate, video]);

    // Gyro look-around — live, no rebuild.
    useEffect(() => {
        applyOrientation(Boolean(orientation));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [orientation, video]);

    const centerDot = showCenterDot ? (
        <div
            style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: 'red',
                transform: 'translate(-50%, -50%)',
                zIndex: 100,
                pointerEvents: 'none',
            }}
        />
    ) : null;

    return (
        <div
            className={
                hideLoadingSpinner
                    ? 'dash-pannellum dash-pannellum-no-spinner'
                    : 'dash-pannellum'
            }
            style={{position: 'relative', width, height}}
        >
            {video ? (
                <video
                    id={id}
                    ref={viewerRef}
                    className="video-js vjs-default-skin vjs-big-play-centered"
                    playsInline
                    crossOrigin="anonymous"
                    poster={video.poster}
                    style={{width: '100%', height: '100%'}}
                />
            ) : (
                <div
                    id={id}
                    ref={viewerRef}
                    style={{width: '100%', height: '100%'}}
                />
            )}
            {centerDot}
        </div>
    );
};

DashPannellum.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * The width of the panorama viewer (any CSS size, e.g. '100%' or '600px').
     */
    width: PropTypes.string,

    /**
     * The height of the panorama viewer (any CSS size, e.g. '400px').
     */
    height: PropTypes.string,

    /**
     * Configuration object for tour mode. Follows the Pannellum tour format:
     * {default: {firstScene, ...}, scenes: {sceneId: {...scene config}}}.
     * A single equirectangular panorama is a tour with one scene.
     * A scene may set `panoramaCanvasId` (the DOM id of a <canvas> element)
     * instead of `panorama` to use Pannellum's dynamic mode: redraw the
     * canvas and the sphere updates in place — no rebuild, no camera reset.
     * Pair with the `dynamicUpdate` prop.
     */
    tour: PropTypes.object,

    /**
     * Configuration object for multi-resolution (tiled) panoramas:
     * {basePath, path, fallbackPath, extension, tileResolution, maxLevel,
     * cubeResolution}.
     */
    multiRes: PropTypes.object,

    /**
     * Configuration object for 360° video panoramas, rendered through
     * video.js: {sources: [{src, type}], poster}.
     */
    video: PropTypes.shape({
        sources: PropTypes.arrayOf(
            PropTypes.shape({
                src: PropTypes.string.isRequired,
                type: PropTypes.string.isRequired,
            })
        ).isRequired,
        poster: PropTypes.string,
    }),

    /**
     * If true, hides the built-in zoom/fullscreen controls so you can build
     * your own controls with Dash components.
     */
    customControls: PropTypes.bool,

    /**
     * If true, displays a center dot in the panorama viewer — useful as a
     * crosshair when authoring hotspot positions.
     */
    showCenterDot: PropTypes.bool,

    /**
     * If true, automatically loads the panorama without user interaction.
     */
    autoLoad: PropTypes.bool,

    /**
     * If true, displays a compass in the panorama viewer.
     */
    compass: PropTypes.bool,

    /**
     * The offset, in degrees, of the center of the panorama from North.
     */
    northOffset: PropTypes.number,

    /**
     * If true, loads the video.js HTTP streaming plugin so HLS/DASH sources
     * (e.g. live streams) can be played as 360° video.
     */
    useHttpStreaming: PropTypes.bool,

    /**
     * Extra hotspots that report clicks back to Dash. Keys are scene IDs,
     * values are arrays of hotspot objects ({pitch, yaw, type, text, name}).
     * Clicking one updates the `lastClickedHotspot` prop.
     */
    callbackHotspots: PropTypes.objectOf(
        PropTypes.arrayOf(
            PropTypes.shape({
                pitch: PropTypes.number.isRequired,
                yaw: PropTypes.number.isRequired,
                type: PropTypes.string.isRequired,
                text: PropTypes.string,
                name: PropTypes.string.isRequired,
            })
        )
    ),

    /**
     * Imperative camera write — set {pitch, yaw, hfov, animated} to pan/zoom
     * the existing viewer without rebuilding it. Omitted fields keep their
     * current value; `animated` is the transition duration in ms (default
     * 1000, use a small value for joystick-style continuous steering).
     * Image panorama modes only.
     */
    lookAt: PropTypes.exact({
        pitch: PropTypes.number,
        yaw: PropTypes.number,
        hfov: PropTypes.number,
        animated: PropTypes.number,
    }),

    /**
     * Imperative scene switch — set to a scene ID from the tour config to
     * load that scene without rebuilding the viewer. Unknown IDs and the
     * already-active scene are ignored.
     */
    loadScene: PropTypes.string,

    /**
     * If true, suppresses Pannellum's "Loading..." box for this viewer —
     * useful with preloaded scenes or data-URI panoramas where the flash
     * is the only visible part of an otherwise instant transition.
     */
    hideLoadingSpinner: PropTypes.bool,

    /**
     * If true (default), the other scenes' panorama images are prefetched
     * into the browser cache once the viewer is up, so tour jumps don't
     * show a loading box.
     */
    preloadScenes: PropTypes.bool,

    /**
     * If true, the viewer re-uploads its panorama texture every frame —
     * required for scenes backed by a live <canvas> (`panoramaCanvasId`).
     * This is the movement-mechanics primitive: redraw the canvas from a
     * game loop and the sphere follows with no rebuild. Leave false for
     * static panoramas.
     */
    dynamicUpdate: PropTypes.bool,

    /**
     * Request gyroscope look-around (device orientation). Works on mobile
     * devices with motion sensors; Pannellum runs the iOS 13+ permission
     * prompt when needed, so on iOS set this to true from a clientside
     * callback on a direct user tap. Whether it actually engaged is
     * reported through `orientationSupported` and `orientationActive`.
     */
    orientation: PropTypes.bool,

    /**
     * Read-only. True when the device/browser can drive the camera from
     * the gyroscope (requires motion sensors and a mobile browser).
     */
    orientationSupported: PropTypes.bool,

    /**
     * Read-only. True while gyro look-around is actively steering the
     * camera (false if permission was denied or `orientation` is off).
     */
    orientationActive: PropTypes.bool,

    /**
     * Read-only. True once the panorama has loaded.
     */
    loaded: PropTypes.bool,

    /**
     * Read-only. The current pitch of the panorama view, in degrees.
     */
    pitch: PropTypes.number,

    /**
     * Read-only. The current horizontal field of view (zoom), in degrees.
     */
    hfov: PropTypes.number,

    /**
     * Read-only. The current yaw of the panorama view, in degrees.
     */
    yaw: PropTypes.number,

    /**
     * Read-only. The ID of the current scene in tour mode.
     */
    currentScene: PropTypes.string,

    /**
     * Read-only. The name of the last clicked callback hotspot.
     */
    lastClickedHotspot: PropTypes.string,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,
};

export default DashPannellum;
