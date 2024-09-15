# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashPannellum(Component):
    """A DashPannellum component.


Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- autoLoad (boolean; default True):
    If True, automatically loads the panorama without user
    interaction.

- compass (boolean; default False):
    If True, displays a compass in the panorama viewer.

- currentScene (string; optional):
    The ID of the current scene in tour mode.

- customControls (boolean; default False):
    If True, enables custom controls for the panorama viewer.

- height (string; default '400px'):
    The height of the panorama viewer.

- multiRes (dict; optional):
    Configuration object for multi-resolution panoramas.

- northOffset (number; default 0):
    The offset, in degrees, of the center of the panorama from North.

- pitch (number; optional):
    The current pitch of the panorama view.

- showCenterDot (boolean; default False):
    If True, displays a center dot in the panorama viewer.

- tour (dict; optional):
    Configuration object for the tour mode.

- useHttpStreaming (boolean; default False):
    If True, enables HTTP streaming support for video.

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
    def __init__(self, id=Component.UNDEFINED, width=Component.UNDEFINED, height=Component.UNDEFINED, tour=Component.UNDEFINED, multiRes=Component.UNDEFINED, video=Component.UNDEFINED, customControls=Component.UNDEFINED, showCenterDot=Component.UNDEFINED, autoLoad=Component.UNDEFINED, compass=Component.UNDEFINED, northOffset=Component.UNDEFINED, pitch=Component.UNDEFINED, yaw=Component.UNDEFINED, currentScene=Component.UNDEFINED, useHttpStreaming=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'autoLoad', 'compass', 'currentScene', 'customControls', 'height', 'multiRes', 'northOffset', 'pitch', 'showCenterDot', 'tour', 'useHttpStreaming', 'video', 'width', 'yaw']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'autoLoad', 'compass', 'currentScene', 'customControls', 'height', 'multiRes', 'northOffset', 'pitch', 'showCenterDot', 'tour', 'useHttpStreaming', 'video', 'width', 'yaw']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashPannellum, self).__init__(**args)
