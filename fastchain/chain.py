import re
import logging
from types import MappingProxyType
from weakref import WeakValueDictionary as WeakDict
from typing import Callable, Pattern
from .chainable import CHAINABLE_OBJECTS, parse
from .monitoring import ReportDetails, Report

CHAIN_NAME: Pattern[str] = re.compile(r'^\w[\w\d_-]*?$', re.DOTALL)


class Chain:
    __slots__ = (
        '__weakref__',
        '__name',
        '__core',
        'create_report',
        'logger'
    )

    def __init__(
            self,
            name: str,
            *chainables: CHAINABLE_OBJECTS,
            log: bool = True
    ):
        """
        creates a chain and globally registers it.

        :param name: the chains name must be unique.
        :param chainables: any supported 'chainable' object.
        :key log: whether to log failures or not, default to True.
        """
        if not isinstance(name, str):
            raise TypeError("the name of the chain must be a string.")
        elif CHAIN_NAME.match(name):
            raise ValueError("chain's name must begin with a letter and only contain letter, digits, _ and -")
        elif name in __chains__:
            raise ValueError("a chain with the same name already exists.")
        self.__name: str = name
        self.logger: logging.Logger | None = logging.getLogger(name) if log else None
        self.__core = parse(chainables, logger=self.logger)
        nodes = tuple(self.__core.nodes())
        required_nodes = len([filter(lambda node: not node.optional, nodes)])
        self.create_report: Callable[[], Report] = lambda: Report(nodes, required_nodes)
        __chains__[name] = self

    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        return self.__name

    def __repr__(self) -> str:
        return f'<Chain {self.__name!r}: {self.__core!r}>'

    def __call__(self, input, reports: dict[str, ReportDetails] | None = None):
        """
        processes the given input and returns the result,
        the chain creates its report and only registers it
        if reports is not None.

        :param input: the entry data to be processed
        :param reports: a dictionary where to register the execution statistics.
        :return: the output result from given input.
        """
        report = self.create_report()
        _, result = self.__core(input, report=report)
        if reports is not None:
            reports[self.__name] = report.make()
        return result


__chains__: WeakDict[str, Chain] = WeakDict()
chains: MappingProxyType[str, Chain] = MappingProxyType(__chains__)


def get_chain(name: str) -> Chain | None:
    """gets chain by name if exists or None otherwise."""
    return __chains__.get(name, None)
