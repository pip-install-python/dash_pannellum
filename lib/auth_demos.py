"""Teaser demos for the authentication gate cards.

Each auth-gated docs page can register ONE live example that renders inside
the sign-in card (lib.gate_layouts.sign_in_layout) — an interactive taste of
what's behind the gate, with no code and no surrounding docs.

The modules referenced here are the same ``.. exec::`` example modules the
docs pages use (they expose a module-level ``component``), so they're already
imported — and their callbacks already registered — when pages/markdown.py
parses the docs at startup. Only one layout (gate card OR full docs) renders
per request, so sharing the component instances never duplicates IDs.

The table ships with ONE working entry in the template — the pattern, live —
and each satellite swaps in its own hero example (one entry is plenty; this
is a funnel, not a gallery). An empty table is legitimate too: cards render
without the demo block. Either way tests/test_auth_demos.py holds the line —
every entry that IS here must resolve on THIS site, because build_demo below
degrades silently by design.

Entries:
    endpoint -> {
        "module":     dotted path of the example module,
        "caption":    short label shown next to the "Live demo" badge,
        "max_height": px cap for the demo viewport inside the card,
        "height":     optional explicit px height — needed by components that
                      size to their container,
    }
"""
from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)

# EMPTY on purpose (2026-08-26). The inherited template entry —
# /examples/visualization -> docs.data-visualization.basic_chart — named a
# page and a module this site does not have, so its card could never render
# and its warning could never fire (template 1.6.26 item 3). It is deleted,
# not replaced: nothing here is gated. Every docs page declares no `tier:`,
# PAGE_DEFAULT_TIER is unset so the default is `public`, and production
# serves /components/tours, /components/arena, /api and /getting-started 200
# with no "Authentication required" card (measured 2026-08-26). An entry
# pointing at an ungated page would resolve for the test and still never
# render — the same silent-inert shape this item exists to kill.
#
# When a page IS gated (control board, or `tier: auth` frontmatter), one
# entry is the whole job — the hero candidate is the tour, whose example
# module already exposes a module-level `component`:
#
#     "/components/tours": {
#         "module": "docs.tours.tour_example",
#         "caption": "Live 360° virtual tour",
#         "max_height": 420,
#     },
DEMOS: dict[str, dict] = {}


def build_demo(path: str):
    """Return the teaser demo block for ``path``, or None.

    Import/attribute failures degrade to the plain (demo-less) card — a broken
    example must never take down the sign-in funnel.
    """
    spec = DEMOS.get(path)
    if spec is None:
        return None
    try:
        module = importlib.import_module(spec["module"])
        component = getattr(module, "component")
    except Exception as e:
        logger.warning("Auth-gate demo %s failed to load (%s) — card renders "
                       "without it", spec.get("module"), e)
        return None

    import dash_mantine_components as dmc
    from dash_iconify import DashIconify

    return dmc.Box(
        [
            dmc.Group(
                [
                    dmc.Badge(
                        "Live demo — try it",
                        variant="light",
                        color="teal",
                        leftSection=DashIconify(icon="tabler:hand-click", width=13),
                    ),
                    dmc.Text(spec.get("caption", ""), size="sm", c="dimmed"),
                ],
                justify="space-between",
                px="md",
                pt="md",
            ),
            dmc.Box(
                component,
                p="md",
                className="auth-gate-demo",
                style={
                    "maxHeight": f"{spec.get('max_height', 420)}px",
                    "overflowY": "auto",
                    "overflowX": "hidden",
                    **({"height": f"{spec['height']}px"} if "height" in spec else {}),
                },
            ),
        ]
    )
