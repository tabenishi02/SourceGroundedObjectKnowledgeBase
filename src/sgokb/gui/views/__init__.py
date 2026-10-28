"""Qt Widgets views for the SGOKB desktop client."""

from .association_page import AssociationPage
from .evidence_page import EvidencePage
from .main_window import NAVIGATION_ITEMS, MainWindow
from .object_page import ObjectPage
from .registry_page import RegistryPage
from .search_page import SearchPage
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
