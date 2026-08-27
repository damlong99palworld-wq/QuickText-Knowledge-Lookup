"""System services: storage, search, hotkeys, clipboard, selection capture."""

from .storage import KnowledgeStore
from .search import KnowledgeSearch

__all__ = ["KnowledgeStore", "KnowledgeSearch"]
