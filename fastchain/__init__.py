"""
fastchain is a package that provides tools to create ready to use function chains,
the main goal is to ease chaining functions and capture errors without breaking the whole program.
the main user interface tools are Chain class, parse function and the two decorators chainable and funfact.
Chain is the main component, it parses the given model and creates the right execution structure.
it also takes a callback that takes a report as its only parameter.
chains are callables, they take an input and returns the last result.
"""
from .reporter import Failure, Severity, OPTIONAL, INHERIT, NORMAL, REQUIRED
from .tools import cb, node_factory


__version__ = '0.1.0'
