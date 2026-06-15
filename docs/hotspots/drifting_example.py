import dash_mantine_components as dmc
from dash import Input, Output, State, callback, clientside_callback, dcc, html

from dash_pannellum import DashPannellum

component = html.Div(
    [
        DashPannellum(
            id="drift-pano",
            tour={
                "default": {"firstScene": "alma"},
                "scenes": {
                    "alma": {
                        "title": "ALMA Observatory",
                        "type": "equirectangular",
                        "panorama": "https://pannellum.org/images/alma.jpg",
                        "autoLoad": True,
                        "yaw": 117,
                        "pitch": -3,
                        "hfov": 100,
                    }
                },
            },
            callbackHotspots={
                "alma": [
                    {
                        "pitch": -3.0,
                        "yaw": 120.0,
                        "type": "info",
                        "text": "Paramecium — click to catch",
                        "name": "paramecium",
                    }
                ]
            },
            autoLoad=True,
            width="100%",
            height="380px",
        ),
        dmc.Group(
            [
                dmc.Switch(id="drift-on", label="Drift", checked=True, size="sm"),
                dmc.Code("waiting for drift…", id="drift-readout"),
            ],
            mt="sm",
            gap="md",
        ),
        html.Div(id="drift-log"),
        dcc.Interval(id="drift-tick", interval=400),
    ]
)

# Swim the contact along a lazy loop — pure callbackHotspots prop updates.
# Since 0.3.1 a position-only change moves the EXISTING hotspot DOM node
# in place (per-name diff), so the marker drifts instead of teleporting
# through destroy/recreate.
clientside_callback(
    """function(n, on) {
        if (!on) { return window.dash_clientside.no_update; }
        const t = (n || 0) * 0.35;
        const yaw = 120 + 22 * Math.sin(t);
        const pitch = -3 + 5 * Math.sin(t * 0.7 + 1);
        window.dash_clientside.set_props('drift-pano', {callbackHotspots: {
            alma: [{
                pitch: Math.round(pitch * 10) / 10,
                yaw: Math.round(yaw * 10) / 10,
                type: 'info',
                text: 'Paramecium — click to catch',
                name: 'paramecium',
            }],
        }});
        return 'contact at pitch ' + pitch.toFixed(1) + '\\u00b0 \\u00b7 yaw '
            + yaw.toFixed(1) + '\\u00b0';
    }""",
    Output("drift-readout", "children"),
    Input("drift-tick", "n_intervals"),
    State("drift-on", "checked"),
    prevent_initial_call=True,
)


@callback(
    Output("drift-log", "children"),
    Input("drift-pano", "lastClickedHotspot"),
    prevent_initial_call=True,
)
def caught(name):
    return dmc.Alert(
        f"Caught it mid-drift! ({name}) — the moving node is still a live "
        "click target.",
        color="teal",
        mt="sm",
    )
