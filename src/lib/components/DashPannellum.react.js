import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

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
        setProps
    } = props;

    const viewerRef = useRef(null);
    const playerRef = useRef(null);

    useEffect(() => {
        const loadScripts = async () => {
            await loadStylesheet('https://cdn.pannellum.org/2.5/pannellum.css');
            await loadScript('https://cdn.pannellum.org/2.5/pannellum.js');

            if (video) {
                await loadStylesheet('https://vjs.zencdn.net/7.1.0/video-js.css');
                await loadScript('https://vjs.zencdn.net/7.1.0/video.js');
                await loadScript('/assets/videojs-pannellum-plugin.js');  // Ensure this is the correct path to your plugin
            }

            initializeViewer();
        };

        loadScripts();

        return () => {
            if (playerRef.current) {
                if (video) {
                    playerRef.current.dispose();
                } else {
                    playerRef.current.destroy();
                }
            }
        };
    }, [tour, multiRes, video]);

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
            const videojs = window.videojs;
            if (videojs) {
                playerRef.current = videojs(viewerRef.current, {
                    controls: true,
                    autoplay: false,
                    preload: 'auto',
                    width: '100%',
                    height: '100%',
                });

                // Initialize Pannellum with the video.js pannellum plugin
                playerRef.current.on('loadedmetadata', () => {
                    playerRef.current.pannellum({});  // Activate pannellum plugin for 360 video

                    if (setProps) {
                        setProps({ loaded: true });
                    }
                });

                // Set up an interval to update pitch and yaw for the video
                const intervalId = setInterval(() => {
                    if (playerRef.current && playerRef.current.pannellumInstance) {
                        const pitch = playerRef.current.pannellumInstance.getPitch();
                        const yaw = playerRef.current.pannellumInstance.getYaw();
                        if (setProps) {
                            setProps({ pitch, yaw });
                        }
                    }
                }, 100); // Update every 100ms

                return () => clearInterval(intervalId);
            }
        } else {
            let config;
            if (multiRes) {
                config = {
                    type: "multires",
                    multiRes: multiRes
                };
            } else if (tour) {
                config = tour;
            }

            if (config) {
                playerRef.current = window.pannellum.viewer(viewerRef.current, config);

                if (setProps) {
                    setProps({ loaded: true });
                }

                // Set up an interval to update pitch and yaw for the panorama
                const intervalId = setInterval(() => {
                    if (playerRef.current) {
                        const pitch = playerRef.current.getPitch();
                        const yaw = playerRef.current.getYaw();
                        const scene = playerRef.current.getScene();
                        if (setProps) {
                            setProps({ pitch, yaw, currentScene: scene });
                        }
                    }
                }, 100); // Update every 100ms

                return () => clearInterval(intervalId);
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
                >
                    {video.sources.map((source, index) => (
                        <source key={index} src={source.src} type={source.type} />
                    ))}
                </video>
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
    showCenterDot: false
};

DashPannellum.propTypes = {
    id: PropTypes.string,
    width: PropTypes.string,
    height: PropTypes.string,
    tour: PropTypes.object,
    multiRes: PropTypes.object,
    video: PropTypes.shape({
        sources: PropTypes.arrayOf(PropTypes.shape({
            src: PropTypes.string.isRequired,
            type: PropTypes.string.isRequired
        })).isRequired,
        poster: PropTypes.string
    }),
    customControls: PropTypes.bool,
    showCenterDot: PropTypes.bool,
    setProps: PropTypes.func,
    loaded: PropTypes.bool,
    pitch: PropTypes.number,
    yaw: PropTypes.number,
    currentScene: PropTypes.string
};

export default DashPannellum;
