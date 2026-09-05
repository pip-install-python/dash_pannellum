"""/terms — the Terms page (1.6.44 item 15).

Content lives in `pages/legal.py` so both Legal pages share one module and
one renderer; this file is the registration. The single markdown string is
what the browser renders AND what the machine lane is served as `llms_doc` —
a site whose terms say one thing to a reader and another to a crawler has two
sets of terms, and only one was reviewed.
"""
from __future__ import annotations

import dash

from lib import page_tiers, page_visibility
from lib.constants import OG_IMAGE_URL, PAGE_TITLE_PREFIX
from pages.legal import TERMS_DESCRIPTION, TERMS_DOC, _render

dash.register_page(
    __name__,
    path="/terms",
    name="Terms",
    title=PAGE_TITLE_PREFIX + "Terms",
    description=TERMS_DESCRIPTION,
    image_url=OG_IMAGE_URL,
    icon="tabler:file-text",
    category="Legal",
    order=1,
)

LLMS_DOC = TERMS_DOC


def layout(**_kwargs):
    return _render(TERMS_DOC, "m2d-page-terms")


# The full machine record, exactly as pages/changelog.py does it: a
# module-level LLMS_DOC alone leaves the package to discover the page with no
# `lastmod` and outside the control board's llms.txt toggle.
from dash_improve_my_llms import register_page_metadata  # noqa: E402

page_visibility.register_default("/terms", "Terms",
                                 visibility="public", llms_public=True)
page_tiers.register("/terms", "public", llms_public=True)
register_page_metadata(
    path="/terms",
    name="Terms",
    description=TERMS_DESCRIPTION,
    title=PAGE_TITLE_PREFIX + "Terms",
    image_url=OG_IMAGE_URL,
    schema_type="WebPage",
    llms_doc=TERMS_DOC,
)
