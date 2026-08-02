# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args
try:
    from dash.types import NumberType  # noqa: F401
except ImportError:
    # Backwards compatibility for dash<=4.1.0
    if typing.TYPE_CHECKING:
        raise
    NumberType = typing.Union[  # noqa: F401
        typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
    ]

ComponentSingleType = typing.Union[str, int, float, Component, None]
ComponentType = typing.Union[
    ComponentSingleType,
    typing.Sequence[ComponentSingleType],
]


class DashPannellum(Component):
    """A DashPannellum component.
DashPannellum wraps the Pannellum WebGL panorama viewer for Dash.
It supports equirectangular panoramas, guided tours with hotspots,
multi-resolution tiled panoramas and 360° video (via video.js).

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- autoLoad (boolean; default True):
    If True, automatically loads the panorama without user
    interaction.

- callbackHotspots (dict; optional):
    Extra hotspots that report clicks back to Dash. Keys are scene
    IDs, values are arrays of hotspot objects ({pitch, yaw, type,
    text, name}). Clicking one updates the `lastClickedHotspot` prop.

    `callbackHotspots` is a dict with strings as keys and values of
    type list of dicts with keys:

    - pitch (number; required)

    - yaw (number; required)

    - type (string; required)

    - text (string; optional)

    - name (string; required)

- compass (boolean; default False):
    If True, displays a compass in the panorama viewer.

- currentScene (string; optional):
    Read-only. The ID of the current scene in tour mode.

- customControls (boolean; default False):
    If True, hides the built-in zoom/fullscreen controls so you can
    build your own controls with Dash components.

- dynamicUpdate (boolean; default False):
    If True, the viewer re-uploads its panorama texture every frame —
    required for scenes backed by a live <canvas>
    (`panoramaCanvasId`). This is the movement-mechanics primitive:
    redraw the canvas from a game loop and the sphere follows with no
    rebuild. Leave False for static panoramas.

- height (string; default '400px'):
    The height of the panorama viewer (any CSS size, e.g. '400px').

- hfov (number; optional):
    Read-only. The current horizontal field of view (zoom), in
    degrees.

- hideLoadingSpinner (boolean; default False):
    If True, suppresses Pannellum's \"Loading...\" box for this viewer
    — useful with preloaded scenes or data-URI panoramas where the
    flash is the only visible part of an otherwise instant transition.

- lastClickedHotspot (string; optional):
    Read-only. The name of the last clicked callback hotspot.

- loadScene (string; optional):
    Imperative scene switch — set to a scene ID from the tour config
    to load that scene without rebuilding the viewer. Unknown IDs and
    the already-active scene are ignored.

- loaded (boolean; optional):
    Read-only. True once the panorama has loaded.

- lookAt (dict; optional):
    Imperative camera write — set {pitch, yaw, hfov, animated} to
    pan/zoom the existing viewer without rebuilding it. Omitted fields
    keep their current value; `animated` is the transition duration in
    ms (default 1000, use a small value for joystick-style continuous
    steering). Image panorama modes only.

    `lookAt` is a dict with keys:

    - pitch (number; optional)

    - yaw (number; optional)

    - hfov (number; optional)

    - animated (number; optional)

- multiRes (dict; optional):
    Configuration object for multi-resolution (tiled) panoramas:
    {basePath, path, fallbackPath, extension, tileResolution,
    maxLevel, cubeResolution}.

- northOffset (number; default 0):
    The offset, in degrees, of the center of the panorama from North.

- orientation (boolean; default False):
    Request gyroscope look-around (device orientation). Works on
    mobile devices with motion sensors; Pannellum runs the iOS 13+
    permission prompt when needed, so on iOS set this to True from a
    clientside callback on a direct user tap. Whether it actually
    engaged is reported through `orientationSupported` and
    `orientationActive`.

- orientationActive (boolean; optional):
    Read-only. True while gyro look-around is actively steering the
    camera (False if permission was denied or `orientation` is off).

- orientationSupported (boolean; optional):
    Read-only. True when the device/browser can drive the camera from
    the gyroscope (requires motion sensors and a mobile browser).

- pitch (number; optional):
    Read-only. The current pitch of the panorama view, in degrees.

- preloadScenes (boolean; default True):
    If True (default), the other scenes' panorama images are
    prefetched into the browser cache once the viewer is up, so tour
    jumps don't show a loading box.

- showCenterDot (boolean; default False):
    If True, displays a center dot in the panorama viewer — useful as
    a crosshair when authoring hotspot positions.

- tour (dict; optional):
    Configuration object for tour mode. Follows the Pannellum tour
    format: {default: {firstScene, ...}, scenes: {sceneId: {...scene
    config}}}. A single equirectangular panorama is a tour with one
    scene. A scene may set `panoramaCanvasId` (the DOM id of a
    <canvas> element) instead of `panorama` to use Pannellum's dynamic
    mode: redraw the canvas and the sphere updates in place — no
    rebuild, no camera reset. Pair with the `dynamicUpdate` prop.

- useHttpStreaming (boolean; default False):
    If True, loads the video.js HTTP streaming plugin so HLS/DASH
    sources (e.g. live streams) can be played as 360° video.

- video (dict; optional):
    Configuration object for 360° video panoramas, rendered through
    video.js: {sources: [{src, type}], poster}.

    `video` is a dict with keys:

    - sources (list of dicts; required)

        `sources` is a list of dicts with keys:

        - src (string; required)

        - type (string; required)

    - poster (string; optional)

- width (string; default '600px'):
    The width of the panorama viewer (any CSS size, e.g. '100%' or
    '600px').

- yaw (number; optional):
    Read-only. The current yaw of the panorama view, in degrees."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_pannellum'
    _type = 'DashPannellum'
    VideoSources = TypedDict(
        "VideoSources",
            {
            "src": str,
            "type": str
        }
    )

    Video = TypedDict(
        "Video",
            {
            "sources": typing.Sequence["VideoSources"],
            "poster": NotRequired[str]
        }
    )

    CallbackHotspots = TypedDict(
        "CallbackHotspots",
            {
            "pitch": NumberType,
            "yaw": NumberType,
            "type": str,
            "text": NotRequired[str],
            "name": str
        }
    )

    LookAt = TypedDict(
        "LookAt",
            {
            "pitch": NotRequired[NumberType],
            "yaw": NotRequired[NumberType],
            "hfov": NotRequired[NumberType],
            "animated": NotRequired[NumberType]
        }
    )


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        width: typing.Optional[str] = None,
        height: typing.Optional[str] = None,
        tour: typing.Optional[dict] = None,
        multiRes: typing.Optional[dict] = None,
        video: typing.Optional["Video"] = None,
        customControls: typing.Optional[bool] = None,
        showCenterDot: typing.Optional[bool] = None,
        autoLoad: typing.Optional[bool] = None,
        compass: typing.Optional[bool] = None,
        northOffset: typing.Optional[NumberType] = None,
        useHttpStreaming: typing.Optional[bool] = None,
        callbackHotspots: typing.Optional[typing.Dict[typing.Union[str, float, int], typing.Sequence["CallbackHotspots"]]] = None,
        lookAt: typing.Optional["LookAt"] = None,
        loadScene: typing.Optional[str] = None,
        hideLoadingSpinner: typing.Optional[bool] = None,
        preloadScenes: typing.Optional[bool] = None,
        dynamicUpdate: typing.Optional[bool] = None,
        orientation: typing.Optional[bool] = None,
        orientationSupported: typing.Optional[bool] = None,
        orientationActive: typing.Optional[bool] = None,
        loaded: typing.Optional[bool] = None,
        pitch: typing.Optional[NumberType] = None,
        hfov: typing.Optional[NumberType] = None,
        yaw: typing.Optional[NumberType] = None,
        currentScene: typing.Optional[str] = None,
        lastClickedHotspot: typing.Optional[str] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'autoLoad', 'callbackHotspots', 'compass', 'currentScene', 'customControls', 'dynamicUpdate', 'height', 'hfov', 'hideLoadingSpinner', 'lastClickedHotspot', 'loadScene', 'loaded', 'lookAt', 'multiRes', 'northOffset', 'orientation', 'orientationActive', 'orientationSupported', 'pitch', 'preloadScenes', 'showCenterDot', 'tour', 'useHttpStreaming', 'video', 'width', 'yaw']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'autoLoad', 'callbackHotspots', 'compass', 'currentScene', 'customControls', 'dynamicUpdate', 'height', 'hfov', 'hideLoadingSpinner', 'lastClickedHotspot', 'loadScene', 'loaded', 'lookAt', 'multiRes', 'northOffset', 'orientation', 'orientationActive', 'orientationSupported', 'pitch', 'preloadScenes', 'showCenterDot', 'tour', 'useHttpStreaming', 'video', 'width', 'yaw']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashPannellum, self).__init__(**args)

setattr(DashPannellum, "__init__", _explicitize_args(DashPannellum.__init__))
