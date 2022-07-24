from typing import Callable, overload, TypeVar, Any

from ._tools import validate_name
from .factory import parse
from .chainables import CHAINABLE_OBJECTS
from .monitoring import ReportDetails, Report, create_report_maker

LOG_FAILURES: bool = True
RAIS_FOR_FAIL: bool = False

T = TypeVar('T')


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
        creates a new chain with the given structure.

        :param name: the chains name must be unique.
        :param chainables: any supported 'chainable' object.
        :key log_failures: whether to log failures or not, default to True.
        :key raise_for_fail: whether to raise exception for fatal failures (default None).
        """
        validate_name(name)
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

    def __call__(self, input: Any, reports: dict[str, ReportDetails] | None = None) -> Any:
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


class ChainMaker:
    """
    Utility object for making a group of chains with the same configuration and same prefix.
    """
    __slots__ = 'name', 'log_failures', 'raise_for_fail', '__registered_chains__'

    def __init__(self, name: str, *, log_failures: bool = LOG_FAILURES, raise_for_fail: bool = RAIS_FOR_FAIL):
        self.name: str = validate_name(name)
        self.log_failures: bool = log_failures
        self.raise_for_fail: bool = raise_for_fail
        self.__registered_chains__: dict[str, Chain] = {}

    @staticmethod
    def _case_insensitive_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("a name should be str")
        return name.lower()

    def __getitem__(self, name: str) -> Chain:
        try:
            return self.__registered_chains__[self._case_insensitive_name(name)]
        except KeyError:
            raise KeyError(f"no chain is registered with the name {name!r}")

    def __contains__(self, name: str) -> bool:
        return self._case_insensitive_name(name) in self.__registered_chains__

    @overload
    def get(self, name: str) -> Chain | None: ...
    @overload
    def get(self, name: str, default: T) -> Chain | T: ...

    def get(self, name, default=None):
        """
        gets the registered chain by name, or returns default if it does not exist.

        :param name: the name of the registered chain (case-insensitive).
        :param default: the value to return if the chain does not exist, default None.
        :return: the chain if it exists or default.
        """
        return self.__registered_chains__.get(self._case_insensitive_name(name), default)

    def __call__(self, name: str, *chainables: CHAINABLE_OBJECTS) -> Chain:
        """
        creates a new chain with the same configuration and same prefix.

        :param name: the name of the new chain.
        :param chainables: the body of the new chain.
        :return: the new created chain.
        """
        if name in self:
            raise ValueError("a chain with the same name already been registered.")
        return Chain(
            f"{self.name}_{validate_name(name)}",
            *chainables,
            log_failures=self.log_failures,
            raise_for_fail=self.raise_for_fail
        )
