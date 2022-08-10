"""
This package contains the implementation of elementary chain components
that perform the processing.

Users are not expected to interact directly with those components and
that should be handled by the chain and other helper function
in factory.py module.
"""

from .base import CHAINABLE, ChainableObject, Chainable, Node, Pass
from .collections import ChainableCollection, Collection, Sequence, DictModel, ListModel, Match
from .options import OptionMap


PASS: Pass = Pass('pass')

__all__ = (
    'CHAINABLE',
    'Chainable',
    'Node',
    'Collection',
    'Sequence',
    'DictModel',
    'ListModel',
    'Match',
    'PASS',
    'ChainableObject',
    'ChainableCollection',
    'OptionMap',
)
