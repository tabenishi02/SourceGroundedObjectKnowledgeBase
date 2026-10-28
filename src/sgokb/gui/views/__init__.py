"""Qt Widgets views for the SGOKB desktop client."""

from . import search_page as _search_page
from .search_page_derivation import SearchPage

# MainWindow imports SearchPage from ``search_page`` directly. Patch that module-level
# symbol before importing MainWindow so every GUI entry path receives the amended page.
_search_page.SearchPage = SearchPage

from .association_page import AssociationPage
from .evidence_page import EvidencePage
from .main_window import NAVIGATION_ITEMS, MainWindow
from .object_page import ObjectPage
from .registry_page import RegistryPage
from .source_page import SourcePage

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
