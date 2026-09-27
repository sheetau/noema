"""Noema's formal language has no machine-learning runtime dependency."""
from .grammar import parse, format_graph
from .semantics import normalize, SemanticError

__all__ = ["parse", "format_graph", "normalize", "SemanticError"]
__version__ = "0.1.0"
