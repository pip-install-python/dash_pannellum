/*
 * Video.js plugin for Pannellum
 * Copyright (c) 2015-2018 Matthew Petroff
 * MIT License
 */

export function initializePlugin() {
    // if (typeof videojs === 'undefined' || typeof pannellum === 'undefined') {
    //     console.error('Video.js or Pannellum is not loaded');
    //     return;
    // }

    var registerPlugin = videojs?.registerPlugin;
    if (!registerPlugin) {
        console.error('Video.js plugin registration method not found');
        return;
    }

    registerPlugin('pannellum', function(config) {
        // Create Pannellum instance
        var player = this;
        var container = player.el();
        var vid = container.getElementsByTagName('video')[0],
            pnlmContainer = document.createElement('div');
        pnlmContainer.style.zIndex = '0';
        config = config || {};
        config.type = 'equirectangular';
        config.dynamic = true;
        config.showZoomCtrl = false;
        config.showFullscreenCtrl = false;
        config.autoLoad = true;
        config.panorama = vid;
        pnlmContainer.style.visibility = 'hidden';
        player.pnlmViewer = pannellum.viewer(pnlmContainer, config);
        container.insertBefore(pnlmContainer, container.firstChild);
        vid.style.display = 'none';

        // Handle update settings
        player.on('play', function() {
            if (vid.readyState > 1)
                player.pnlmViewer.setUpdate(true);
        });
        player.on('canplay', function() {
            if (!player.paused())
                player.pnlmViewer.setUpdate(true);
        });
        player.on('pause', function() {
            player.pnlmViewer.setUpdate(false);
        });
        player.on('loadeddata', function() {
            pnlmContainer.style.visibility = 'visible';
        });
        player.on('seeking', function() {
            if (player.paused())
                player.pnlmViewer.setUpdate(true);
        });
        player.on('seeked', function() {
            if (player.paused())
                player.pnlmViewer.setUpdate(false);
        });

        // Add methods to get pitch and yaw
        // player.pannellum = function(method) {
        //     if (method === 'getPitch') {
        //         return player.pnlmViewer.getPitch();
        //     } else if (method === 'getYaw') {
        //         return player.pnlmViewer.getYaw();
        //     }
        // };
    });
}

// Check if videojs is already available, if not, wait for it
window.addEventListener('load', () => {
    setTimeout(() => {
        if (typeof videojs !== 'undefined' && typeof pannellum !== 'undefined') {
            initializePlugin();
        }
    }, 100); // Delay to ensure everything is loaded
});