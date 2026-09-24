"""Retrieval-augmented generation package.

The package initializer intentionally avoids importing cloud-backed services so
local retrieval modules remain independently testable.
"""

from .index import VectorIndex

__all__ = ["VectorIndex"]
