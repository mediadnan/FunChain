"""
this module implement option functions, those are functions that get applied
to chainables and either alter their properties or modify some behaviour.

the module also contains a mapping of symbols to specific functions
to serve as shortcuts to those functions.
"""
from types import MappingProxyType
from typing import Iterable, Callable

from .base import ChainableObject
from .._abc import ReporterBase


def optional(self: ChainableObject) -> ChainableObject:
    """sets the chainable as optional"""
    self.optional = True
    return self


def for_each(chainable: ChainableObject) -> ChainableObject:
    """modifies chainable process method to be applied in iteration"""
    def _process_each(inputs, reporter):
        for input in inputs:
            success, result = _process(input, reporter)
            if success:
                yield result

    def process(self: ChainableObject, inputs, reporter: ReporterBase) -> tuple[bool, Iterable]:
        try:
            iter(inputs)
        except TypeError as error:
            self.failure(inputs, error, reporter)
            return False, ()
        return True, _process_each(inputs, reporter)
    _process = getattr(chainable, 'process')
    setattr(chainable, 'process', process.__get__(chainable, chainable.__class__))
    return chainable


OptionMap: MappingProxyType[str, Callable[[ChainableObject], ChainableObject]] = MappingProxyType({
    '?': optional,
    '*': for_each
})
