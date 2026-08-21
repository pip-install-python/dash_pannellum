---
name: 360° Video
description: Play equirectangular 360° video through video.js, including HLS/DASH HTTP streaming
endpoint: /components/video
package: dash_pannellum
icon: mdi:video
lastmod: 2026-08-02
---

.. llms_copy::360° Video

.. toc::

### Overview

Pass a `video` configuration and DashPannellum switches to **video mode**: the panorama becomes a [video.js](https://videojs.com/) player whose frames are projected onto the Pannellum sphere. You get the standard video.js transport controls (play/pause, scrubber, volume) plus full drag-to-look-around.

Provide multiple `sources` and the browser picks the first format it can decode:

.. exec::docs.video.video_example
    :code: false

Press play, then drag the picture while it runs.

.. source::docs/video/video_example.py
    :defaultExpanded: false
    :withExpandedButton: true

---

### Configuration

```python
video = {
    "sources": [
        {"src": "https://example.com/pano.webm", "type": "video/webm"},
        {"src": "https://example.com/pano.mp4",  "type": "video/mp4"},
    ],
    "poster": "https://example.com/poster.jpg",   # optional preview frame
}
```

- **`sources`** *(required)* — list of `{src, type}` entries, tried in order.
- **`poster`** *(optional)* — image shown before playback starts.

The video file itself must be **equirectangular** (2:1 aspect ratio) for the projection to look right.

---

### HTTP streaming (HLS / DASH)

For live sources or adaptive bitrate streams, set `useHttpStreaming=True`. The component loads the video.js [http-streaming](https://github.com/videojs/http-streaming) plugin and overrides native HLS handling:

```python
DashPannellum(
    id="live-360",
    video={
        "sources": [
            {"src": "https://example.com/stream.m3u8", "type": "application/x-mpegURL"},
        ],
    },
    useHttpStreaming=True,
)
```

.. admonition::Cross-origin video
    :icon: mdi:shield-alert-outline
    :color: yellow

    WebGL needs pixel access to the video frames, so the video server must send permissive CORS headers (`Access-Control-Allow-Origin`). The component already sets `crossOrigin="anonymous"` on the underlying `<video>` element.
