// import React, { useEffect, useRef } from 'react';
// import PropTypes from 'prop-types';
// import {initializePlugin} from "../index";
//
// /**
//  * DashPannellum is a component for displaying panoramic images and videos.
//  * It supports various modes including tours, multi-resolution images, and 360° videos.
//  */
// const DashPannellum = (props) => {
//     const {
//         id,
//         width,
//         height,
//         tour,
//         multiRes,
//         video,
//         customControls,
//         showCenterDot,
//         autoLoad,
//         compass,
//         northOffset,
//         setProps
//     } = props;
//
//     const viewerRef = useRef(null);
//     const playerRef = useRef(null);
//     const initializedRef = useRef(false);
//
//     useEffect(() => {
//         if (!initializedRef.current) {
//             const loadScripts = async () => {
//                 try {
//                     await loadStylesheet('https://cdn.pannellum.org/2.5/pannellum.css');
//                     await loadScript('https://cdn.pannellum.org/2.5/pannellum.js');
//
//                     if (video) {
//                         await loadStylesheet('https://vjs.zencdn.net/7.20.3/video-js.min.css');
//                         await loadScript('https://vjs.zencdn.net/7.20.3/video.min.js');
//
//                         await new Promise(resolve => {
//                             const checkVideojs = () => {
//                                 if (window.videojs) {
//                                     initializePlugin();
//                                     resolve();
//                                 } else {
//                                     setTimeout(checkVideojs, 50);
//                                 }
//                             };
//                             checkVideojs();
//                         });
//
//                         initializePlugin();
//                         // Add a small delay to ensure the plugin is fully initialized
//                         await new Promise(resolve => setTimeout(resolve, 100));
//                     }
//
//                     initializeViewer();
//                     initializedRef.current = true;
//                 } catch (error) {
//                     console.error('Error loading scripts:', error);
//                 }
//             };
//
//             loadScripts().then(r => console.log('Scripts loaded')).catch(e => console.error('Error loading scripts:', e));
//         }
//
//         return () => {
//             if (playerRef.current) {
//                 if (video) {
//                     playerRef.current.dispose();
//                 } else {
//                     playerRef.current.destroy();
//                 }
//             }
//         };
//     }, [tour, multiRes, video, autoLoad,  compass, northOffset]);
//
//     const loadScript = (src) => {
//         return new Promise((resolve, reject) => {
//             const script = document.createElement('script');
//             script.src = src;
//             script.async = true;
//             script.onload = resolve;
//             script.onerror = reject;
//             document.body.appendChild(script);
//         });
//     };
//
//     const loadStylesheet = (href) => {
//         return new Promise((resolve, reject) => {
//             const link = document.createElement('link');
//             link.rel = 'stylesheet';
//             link.href = href;
//             link.onload = resolve;
//             link.onerror = reject;
//             document.head.appendChild(link);
//         });
//     };
//
//     const initializeViewer = () => {
//         if (video) {
//             console.log('Initializing video panorama');
//             const videojs = window.videojs;
//             if (videojs) {
//                 console.log('Video.js found, creating player');
//                 playerRef.current = videojs(viewerRef.current, {
//                     controls: true,
//                     autoplay: false,
//                     preload: autoLoad ? 'auto' : 'metadata',
//                     width: '100%',
//                     height: '100%',
//                 });
//
//                 // Initialize Pannellum with the video.js pannellum plugin
//                 playerRef.current.on('loadedmetadata', () => {
//                     playerRef.current.pannellum({ autoLoad: autoLoad });
//
//                     if (setProps) {
//                         setProps({ loaded: true });
//                     }
//                 });
//
//                 // Set up an interval to update pitch and yaw for the video
//                 // const intervalId = setInterval(() => {
//                 //     if (playerRef.current && playerRef.current.pannellum) {
//                 //         const pitch = playerRef.current.pannellum('getPitch');
//                 //         const yaw = playerRef.current.pannellum('getYaw');
//                 //         if (setProps) {
//                 //             setProps({ pitch, yaw });
//                 //         }
//                 //     }
//                 // }, 100); // Update every 100ms
//
//                 return () => clearInterval(intervalId);
//             }
//         } else {
//             console.log('Initializing non-video panorama');
//             let config;
//             if (multiRes) {
//                 config = {
//                     type: "multires",
//                     multiRes: multiRes,
//                     autoLoad: autoLoad,
//                     compass: compass,
//                     northOffset: northOffset
//                 };
//             } else if (tour) {
//                 config = {
//                     ...tour,
//                     autoLoad: autoLoad,
//                     compass: compass,
//                     northOffset: northOffset
//                 };
//             }
//
//             if (config) {
//                 playerRef.current = window.pannellum.viewer(viewerRef.current, config);
//
//                 if (setProps) {
//                     setProps({ loaded: autoLoad });
//                 }
//
//                 // Set up an interval to update pitch and yaw for non-video panoramas
//                 const intervalId = setInterval(() => {
//                     if (playerRef.current) {
//                         const pitch = playerRef.current.getPitch();
//                         const yaw = playerRef.current.getYaw();
//                         const scene = playerRef.current.getScene();
//                         if (setProps) {
//                             setProps({ pitch, yaw, currentScene: scene });
//                         }
//                     }
//                 }, 100); // Update every 100ms
//
//                 return () => clearInterval(intervalId);
//             }
//         }
//     };
//
//     const renderCenterDot = () => {
//         if (!showCenterDot) return null;
//
//         return (
//             <div style={{
//                 position: 'absolute',
//                 top: '50%',
//                 left: '50%',
//                 width: '10px',
//                 height: '10px',
//                 borderRadius: '50%',
//                 backgroundColor: 'red',
//                 transform: 'translate(-50%, -50%)',
//                 zIndex: 100,
//                 pointerEvents: 'none'
//             }} />
//         );
//     };
//
//     return (
//         <div style={{ position: 'relative', width, height }}>
//             {video ? (
//                 <video
//                     id={id}
//                     ref={viewerRef}
//                     className="video-js vjs-default-skin vjs-big-play-centered"
//                     playsInline
//                     crossOrigin="anonymous"
//                     poster={video.poster}
//                     style={{ width: '100%', height: '100%' }}
//                 >
//                     {video.sources.map((source, index) => (
//                         <source key={index} src={source.src} type={source.type} />
//                     ))}
//                 </video>
//             ) : (
//                 <div id={id} ref={viewerRef} style={{ width: '100%', height: '100%' }} />
//             )}
//             {renderCenterDot()}
//         </div>
//     );
// };
//
// DashPannellum.defaultProps = {
//     width: '600px',
//     height: '400px',
//     customControls: false,
//     showCenterDot: false,
//     autoLoad: false,
//     compass: false,
//     northOffset: 0
// };
//
// DashPannellum.propTypes = {
//     /**
//      * The ID used to identify this component in Dash callbacks.
//      */
//     id: PropTypes.string,
//
//     /**
//      * The width of the panorama viewer.
//      */
//     width: PropTypes.string,
//
//     /**
//      * The height of the panorama viewer.
//      */
//     height: PropTypes.string,
//
//     /**
//      * Configuration object for the tour mode.
//      */
//     tour: PropTypes.object,
//
//     /**
//      * Configuration object for multi-resolution panoramas.
//      */
//     multiRes: PropTypes.object,
//
//     /**
//      * Configuration object for video panoramas.
//      */
//     video: PropTypes.shape({
//         sources: PropTypes.arrayOf(PropTypes.shape({
//             src: PropTypes.string.isRequired,
//             type: PropTypes.string.isRequired
//         })).isRequired,
//         poster: PropTypes.string
//     }),
//
//     /**
//      * If true, enables custom controls for the panorama viewer.
//      */
//     customControls: PropTypes.bool,
//
//     /**
//      * If true, displays a center dot in the panorama viewer.
//      */
//     showCenterDot: PropTypes.bool,
//
//     /**
//      * Dash-assigned callback that should be called to report property changes
//      * to Dash, to make them available for callbacks.
//      */
//     setProps: PropTypes.func,
//
//     /**
//      * If true, automatically loads the panorama without user interaction.
//      */
//     autoLoad: PropTypes.bool,
//
//     /**
//      * If true, displays a compass in the panorama viewer.
//      */
//     compass: PropTypes.bool,
//
//     /**
//      * The offset, in degrees, of the center of the panorama from North.
//      */
//     northOffset: PropTypes.number,
//
//     /**
//      * The current pitch of the panorama view.
//      */
//     pitch: PropTypes.number,
//
//     /**
//      * The current yaw of the panorama view.
//      */
//     yaw: PropTypes.number,
//
//     /**
//      * The ID of the current scene in tour mode.
//      */
//     currentScene: PropTypes.string
// };

// export default DashPannellum;

import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import {initializePlugin} from "../index";

const DashPannellum = (props) => {
    const {
        id,
        width,
        height,
        tour,
        multiRes,
        video,
        customControls,
        showCenterDot,
        autoLoad,
        compass,
        northOffset,
        setProps,
        useHttpStreaming
    } = props;

    const viewerRef = useRef(null);
    const playerRef = useRef(null);
    const initializedRef = useRef(false);

    useEffect(() => {
        if (!initializedRef.current) {
            const loadScripts = async () => {
                try {
                    await loadStylesheet('https://cdn.pannellum.org/2.5/pannellum.css');
                    await loadScript('https://cdn.pannellum.org/2.5/pannellum.js');

                    if (video) {
                        await loadStylesheet('https://vjs.zencdn.net/7.20.3/video-js.min.css');
                        await loadScript('https://vjs.zencdn.net/7.20.3/video.min.js');

                        if (useHttpStreaming) {
                            await loadScript('https://unpkg.com/@videojs/http-streaming@2.14.2/dist/videojs-http-streaming.min.js');
                        }

                        await new Promise(resolve => {
                            const checkVideojs = () => {
                                if (window.videojs) {
                                    initializePlugin();
                                    resolve();
                                } else {
                                    setTimeout(checkVideojs, 50);
                                }
                            };
                            checkVideojs();
                        });

                        // Add a small delay to ensure the plugin is fully initialized
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }

                    initializeViewer();
                    initializedRef.current = true;
                } catch (error) {
                    console.error('Error loading scripts:', error);
                }
            };

            loadScripts().then(() => console.log('Scripts loaded')).catch(e => console.error('Error loading scripts:', e));
        }

        return () => {
            if (playerRef.current) {
                if (video) {
                    playerRef.current.dispose();
                } else {
                    playerRef.current.destroy();
                }
            }
        };
    }, [tour, multiRes, video, autoLoad, compass, northOffset, useHttpStreaming]);

    const loadScript = (src) => {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            script.onload = resolve;
            script.onerror = reject;
            document.body.appendChild(script);
        });
    };

    const loadStylesheet = (href) => {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    };

    const initializeViewer = () => {
        if (video) {
            console.log('Initializing video panorama');
            const videojs = window.videojs;
            if (videojs) {
                console.log('Video.js found, creating player');
                const playerOptions = {
                    controls: true,
                    autoplay: true,
                    preload: 'auto',
                    width: '100%',
                    height: '100%',
                    sources: video.sources,
                };

                if (useHttpStreaming) {
                    playerOptions.html5 = {
                        vhs: {
                            overrideNative: true
                        }
                    };
                }

                playerRef.current = videojs(viewerRef.current, playerOptions);

                playerRef.current.ready(() => {
                    playerRef.current.pannellum({
                        autoLoad: autoLoad,
                        showControls: customControls,
                        compass: compass,
                        northOffset: northOffset
                    });

                    if (setProps) {
                        setProps({ loaded: true });
                    }
                });

                playerRef.current.on('loadedmetadata', () => {
                    console.log('Video metadata loaded');
                });

                playerRef.current.on('error', (error) => {
                    console.error('Video.js error:', error);
                });
            }
        } else {
            // Non-video panorama initialization (unchanged)
            console.log('Initializing non-video panorama');
            let config;
            if (multiRes) {
                config = {
                    type: "multires",
                    multiRes: multiRes,
                    autoLoad: autoLoad,
                    compass: compass,
                    northOffset: northOffset
                };
            } else if (tour) {
                config = {
                    ...tour,
                    autoLoad: autoLoad,
                    compass: compass,
                    northOffset: northOffset
                };
            }

            if (config) {
                playerRef.current = window.pannellum.viewer(viewerRef.current, config);

                if (setProps) {
                    setProps({ loaded: autoLoad });
                }
            }
        }
    };

    const renderCenterDot = () => {
        if (!showCenterDot) return null;

        return (
            <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: 'red',
                transform: 'translate(-50%, -50%)',
                zIndex: 100,
                pointerEvents: 'none'
            }} />
        );
    };

    return (
        <div style={{ position: 'relative', width, height }}>
            {video ? (
                <video
                    id={id}
                    ref={viewerRef}
                    className="video-js vjs-default-skin vjs-big-play-centered"
                    playsInline
                    crossOrigin="anonymous"
                    poster={video.poster}
                    style={{ width: '100%', height: '100%' }}
                />
            ) : (
                <div id={id} ref={viewerRef} style={{ width: '100%', height: '100%' }} />
            )}
            {renderCenterDot()}
        </div>
    );
};

DashPannellum.defaultProps = {
    width: '600px',
    height: '400px',
    customControls: false,
    showCenterDot: false,
    autoLoad: true,
    compass: false,
    northOffset: 0,
    useHttpStreaming: false
};

DashPannellum.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * The width of the panorama viewer.
     */
    width: PropTypes.string,

    /**
     * The height of the panorama viewer.
     */
    height: PropTypes.string,

    /**
     * Configuration object for the tour mode.
     */
    tour: PropTypes.object,

    /**
     * Configuration object for multi-resolution panoramas.
     */
    multiRes: PropTypes.object,

    /**
     * Configuration object for video panoramas.
     */
    video: PropTypes.shape({
        sources: PropTypes.arrayOf(PropTypes.shape({
            src: PropTypes.string.isRequired,
            type: PropTypes.string.isRequired
        })).isRequired,
        poster: PropTypes.string
    }),

    /**
     * If true, enables custom controls for the panorama viewer.
     */
    customControls: PropTypes.bool,

    /**
     * If true, displays a center dot in the panorama viewer.
     */
    showCenterDot: PropTypes.bool,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,

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
     * The current pitch of the panorama view.
     */
    pitch: PropTypes.number,

    /**
     * The current yaw of the panorama view.
     */
    yaw: PropTypes.number,

    /**
     * The ID of the current scene in tour mode.
     */
    currentScene: PropTypes.string,

    /**
     * If true, enables HTTP streaming support for video.
     */
    useHttpStreaming: PropTypes.bool
};

export default DashPannellum;