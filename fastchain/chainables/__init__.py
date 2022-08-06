from typing import Callable
from .base import CHAINABLE, ChainableObject, Chainable, Node, Pass, optional
from .collections import ChainableCollection, Collection, Sequence, Model, Group, Match
from .options import Option, Map
from types import MappingProxyType


PASS: Pass = Pass('pass')  # chain_pass singleton

OptionMap: MappingProxyType[str, Callable[[Chainable], Chainable]] = MappingProxyType({
    '?': optional,
    '*': Map
})

__all__ = (
    'CHAINABLE',
    'Chainable',
    'Node',
    'Collection',
    'Sequence',
    'Model',
    'Group',
    'Match',
    'Option',
    'Map',
    'PASS',
    'ChainableObject',
    'ChainableCollection',
    'OptionMap'
)
