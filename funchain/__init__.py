"""
FunChain is a package that provides tools for creating ready to use function chains,
the main goal is to ease chaining functions and capture errors without breaking the whole program.
The main user interface tools are Chain class, parse function and the two decorators chainable and funfact.
Chain is the main component, it parses the given model and creates the right execution structure.
It also takes a callback that takes a report as its only parameter.
Chains are callables, they take an input and return the last result.
"""
from .core import (
    BaseNode,
    Severity,
    chain,
    _node as node,
    loop,
    static,
    optional,
    required,
)
from failures import Reporter   # shortcut # noqa: F401 # pylint: disable=unused-import

__version__ = '0.1.0'
