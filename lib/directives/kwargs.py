import importlib
import inspect
from markdown2dash.src.directives.kwargs import Kwargs as KwargsBase


def convert_docstring_to_dict(docstring):
    """Convert numpy style parameter docstring to a list of dicts with keys name, type, description"""

    lines: list[str] = docstring.split("----------\n")[-1].split("\n")

    params = []
    new_param = None
    for line in lines:
        if not line.startswith("    "):
            if new_param is not None:
                params.append(new_param)
            name, type = line.split(": ", 1)
            new_param = {"name": name, "type": type, "description": ""}
        else:
            new_param["description"] += " " + line.strip()
    params.append(new_param)

    return params


PACKAGE_MAP = {
    "dmc": "dash_mantine_components",
    "html": "dash.html",
    "dcc": "dash.dcc",
    "dash": "dash",
}


def resolve_props(component_spec: str, library: str = "dash_mantine_components") -> list:
    """`[{name, type, description}, ...]` for a `.. kwargs::` target.

    THE ONE PARSE (sync item 18 contract 7, note 80). It has two callers and
    that is the whole point: `Kwargs.hook` below builds the React tree from
    it, and `pages/markdown._expand_kwargs_directives` builds the MARKDOWN
    table the machine lane serves. When those two were separate — when the
    directive only fed the React tree — /api's prop table existed solely in
    the JS-rendered DOM: measured on this host 2026-08-31, all four of
    `northOffset` / `hideLoadingSpinner` / `useHttpStreaming` / `autoLoad`
    present in the layout and absent from /api/llms.txt, the crawler HTML
    and the app-shell markup alike. Every agent got a props page with no
    props.

    Returns [] on any failure: a props table is a nice-to-have, not worth
    failing a page for. `tests/test_api_lane_parity.py` is what stops []
    from being silence — it asserts ROWS, in every lane.
    """
    if "." in component_spec:
        package_abbr, component_name = component_spec.rsplit(".", 1)
        package = PACKAGE_MAP.get(package_abbr, package_abbr)
    else:
        package, component_name = library, component_spec
    try:
        imported = importlib.import_module(package)
        component = getattr(imported, component_name)
        docstring = inspect.getdoc(component)
        if docstring and "----------" in docstring:
            # numpy-style (dash-mantine-components hand-written docs)
            return convert_docstring_to_dict(docstring.split("----------\n")[-1])
        if docstring and "Keyword arguments:" in docstring:
            # dash-generate-components style — every component a library
            # satellite documents, including this repo's own DashPannellum.
            from markdown2dash.src.utils import (
                convert_docstring_to_dict as dash_convert,
            )

            return dash_convert(docstring.split("Keyword arguments:")[-1])
    except Exception:
        pass
    return []


class Kwargs(KwargsBase):

    def hook(self, md, state):
        sections = []

        for tok in state.tokens:
            if tok["type"] == self.block_name:
                sections.append(tok)

        for section in sections:
            attrs = section["attrs"]

            # ONE parse, shared with the prose expansion — see resolve_props.
            attrs["kwargs"] = resolve_props(
                attrs["title"], attrs.pop("library", "dash_mantine_components")
            )
