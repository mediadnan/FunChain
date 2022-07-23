import re
from typing import Callable, Pattern
from .factory import parse
from .chainables import CHAINABLE_OBJECTS
from .monitoring import ReportDetails, Report, create_report_maker

CHAIN_NAME: Pattern[str] = re.compile(r'^\w[\w\d_-]+?$', re.DOTALL)
LOG_FAILURES: bool = True
RAIS_FOR_FAIL: bool = False


class Chain:
    __slots__ = '__name', '__core', '__report_maker',

    def __init__(
            self,
            name: str,
            *chainables: CHAINABLE_OBJECTS,
            log_failures: bool = LOG_FAILURES,
            raise_for_fail: bool = RAIS_FOR_FAIL
    ):
        """
        creates a chain and globally registers it.

        :param name: the chains name must be unique.
        :param chainables: any supported 'chainable' object.
        :key log_failures: whether to log failures or not, default to True.
        """
        if not isinstance(name, str):
            raise TypeError("the name of the chain must be a string.")
        elif not CHAIN_NAME.match(name):
            raise ValueError("chain's name must begin with a letter and only contain letter, digits, _ and -")
        core = parse(chainables)

        self.__name: str = name
        self.__core = core
        self.__report_maker: Callable[[], Report] = create_report_maker(
            core.nodes(),
            log_failures,
            raise_for_fail,
            name=name
        )

    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        return self.__name

    def __repr__(self) -> str:
        return f'<chain {self.__name!r}>'

    def __call__(self, input, reports: dict[str, ReportDetails] | None = None):
        """
        processes the given input and returns the result,
        the chain creates its report and only registers it
        if reports is not None.

        :param input: the entry data to be processed
        :param reports: a dictionary where to register the execution statistics.
        :return: the output result from given input.
        """
        report = self.__report_maker()
        result = self.__core(input, report=report)[1]
        if reports is not None:
            reports[self.__name] = report.make()
        return result
