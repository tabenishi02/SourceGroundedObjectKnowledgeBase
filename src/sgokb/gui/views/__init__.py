"""Qt Widgets views for the SGOKB desktop client."""

from . import search_page as _search_page
from .search_page_derivation import SearchPage

# MainWindow imports SearchPage from ``search_page`` directly. Patch that module-level
# symbol before importing MainWindow so every GUI entry path receives the amended page.
_search_page.SearchPage = SearchPage

# These imports intentionally follow the SearchPage module patch above. MainWindow imports
# SearchPage from ``search_page`` while it is defined, so moving them above the patch would
# bypass the Derivation Kind selector amendment.
from .association_page import AssociationPage  # noqa: E402
from .evidence_page import EvidencePage  # noqa: E402
from .main_window import NAVIGATION_ITEMS, MainWindow  # noqa: E402
from .object_page import ObjectPage  # noqa: E402
from .registry_page import RegistryPage  # noqa: E402
from .source_page import SourcePage  # noqa: E402

__all__ = [
    "AssociationPage",
    "EvidencePage",
    "MainWindow",
    "NAVIGATION_ITEMS",
    "ObjectPage",
    "RegistryPage",
    "SearchPage",
    "SourcePage",
]
