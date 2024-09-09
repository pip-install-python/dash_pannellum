# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashPannellum(Component):
    """A DashPannellum component.
DashPannellum is a component for displaying panoramic images and videos.
It supports various modes including tours, multi-resolution images, and 360° videos.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- currentScene (string; optional):
    The ID of the current scene in tour mode.

- customControls (boolean; default False):
    If True, enables custom controls for the panorama viewer.

- height (string; default '400px'):
    The height of the panorama viewer.

- loaded (boolean; optional):
    Indicates whether the panorama has been loaded.

- multiRes (dict; optional):
    Configuration object for multi-resolution panoramas.

- pitch (number; optional):
    The current pitch of the panorama view.

- showCenterDot (boolean; default False):
    If True, displays a center dot in the panorama viewer.

- tour (dict; optional):
    Configuration object for the tour mode.

- video (dict; optional):
    Configuration object for video panoramas.

    `video` is a dict with keys:

    - poster (string; optional)

    - sources (list of dicts; required)

        `sources` is a list of dicts with keys:

        - src (string; required)

        - type (string; required)

- width (string; default '600px'):
    The width of the panorama viewer.

- yaw (number; optional):
    The current yaw of the panorama view."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_pannellum'
    _type = 'DashPannellum'
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, width=Component.UNDEFINED, height=Component.UNDEFINED, tour=Component.UNDEFINED, multiRes=Component.UNDEFINED, video=Component.UNDEFINED, customControls=Component.UNDEFINED, showCenterDot=Component.UNDEFINED, loaded=Component.UNDEFINED, pitch=Component.UNDEFINED, yaw=Component.UNDEFINED, currentScene=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'currentScene', 'customControls', 'height', 'loaded', 'multiRes', 'pitch', 'showCenterDot', 'tour', 'video', 'width', 'yaw']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'currentScene', 'customControls', 'height', 'loaded', 'multiRes', 'pitch', 'showCenterDot', 'tour', 'video', 'width', 'yaw']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashPannellum, self).__init__(**args)
