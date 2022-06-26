from fastchain.wrapper import chainable, funfact
from fastchain.chain import Chain, parse


__version__ = '1.0.1'
__doc__ = """fastchain package provides tools and classes to create ready to use chains,
the main goal is to ease chaining functions and capture errors without breaking the whole program.

the main user interface tools are Chain class, parse function and the two decorators chainable and funfact.

Chain is the main component, it parses the given model and creates the right execution structure.
it also takes a callback that takes a report as its only parameter.
chains are callables, they take an input and returns the last result."""
__all__ = [
    'chainable',
    'funfact',
    'Chain',
    'parse',
    '__version__'
]
