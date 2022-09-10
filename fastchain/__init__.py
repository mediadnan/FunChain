"""
Fastchain is an open source library that provides tools to quickly and easily create safe data processing pipelines,
isolating each step in  a highly fault-tolerant way,
it supports composing functions sequentially or simultaneously,
and it reports statistics and failures after each execution.

Learn more by visiting the documentation page: https://fast-chain.readthedocs.io/
And visit our source repository on GitHub: https://github.com/mediadnan/FastChain
"""
from .factory import funfact, chainable, match
from .chains import make, get, add_report_handler

__version__ = '0.1.0'
__all__ = 'make', 'get', 'add_report_handler', 'funfact', 'chainable', 'match'
