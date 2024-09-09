# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashPannellum(Component):
    """A DashPannellum component.


Keyword arguments:

- id (string; optional)

- currentScene (string; optional)

- customControls (boolean; default False)

- height (string; default '400px')

- loaded (boolean; optional)

- multiRes (dict; optional)

- pitch (number; optional)

- showCenterDot (boolean; default False)

- tour (dict; optional)

- video (dict; optional)

    `video` is a dict with keys:

    - poster (string; optional)

    - sources (list of dicts; required)

        `sources` is a list of dicts with keys:

        - src (string; required)

        - type (string; required)

- width (string; default '600px')

- yaw (number; optional)"""
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
