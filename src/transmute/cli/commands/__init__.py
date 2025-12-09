"""
CLI commands.
"""

from transmute.cli.commands.translate import translate
from transmute.cli.commands.analyze import analyze
from transmute.cli.commands.strategies import strategies
from transmute.cli.commands.config import config

__all__ = [
    "translate",
    "analyze",
    "strategies",
    "config",
]