"""Git operations for Transmute."""

from transmute.git.repository import GitRepository, detect_platform

__all__ = [
    "GitRepository",
    "detect_platform",
]