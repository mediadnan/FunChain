"""
Fastchain is an open source library that provides tools to quickly and easily create safe data processing pipelines,
isolating side-effects (Exceptions) of each function,
it supports composing functions sequentially or simultaneously,
it has a stat report system for monitoring failures and more...

Learn more about FastChain by visiting its documentation page: https://fast-chain.readthedocs.io/
Or visit its source repository on GitHub: https://github.com/mediadnan/FastChain
"""
from .chain import Chain, ChainMaker
from .factory import funfact, chainable, match

__version__ = '2.0.0'
__all__ = 'ChainMaker', 'Chain', 'funfact', 'chainable', 'match'
