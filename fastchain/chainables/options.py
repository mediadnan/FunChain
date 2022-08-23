"""
This module define functions that customize a chainable object by mutating
its attribute(s) to either change a property or a behaviour.

Users should not bother with this low level details, and those functions
are not more than helper function for the parser to apply an option.

The only object that acts as an interface for this module is 'OptionMap',
a mapping that gets a specific option_function from its specific symbol.
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
    """makes chainable process method to be applied in iteration"""
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
