"""
This module implements the chain object class,
the main object used to define data processing pipelines.
and ChainMaker a factory that produces chains
needed to be grouped and controlled together.

Chain and ChainMaker can be directly imported from fastchain.
"""
import re
import typing as tp
from .chainables import Chainable
from .factory import CHAINABLES, parse
from .monitoring import ReporterMaker, LoggingHandler, ReportStatistics, FailureDetails

T = tp.TypeVar('T')

CHAIN_NAME: tp.Pattern[str] = re.compile(r'^[a-z_](?:\w+[_-]?)+?$', re.IGNORECASE)


def validate_chain_name(name: str, var_name: str = 'name') -> str:
    """validates the chain's name and returns it

    this function only allows names (str of course)
    that has more than one character, starting with
    an ascii letter or _ and only contains letters,
    digits, - and _

    This prevents usage of some special characters
    such as ( : / . [ ] ) that have meaning
    and could be potentially used in future features.

    :param name: the name of the chain
    :type name: str
    :param var_name: the name used in errors
    :type var_name: str
    :return: the same name if it's valid
    :rtype: str
    :raise TypeError: if name has the wrong type other than str
    :raise ValueError: if name doesn't match the requirement
    """
    if not isinstance(name, str):
        raise TypeError(f"{var_name} must be str not {type(name).__name__}")
    elif not CHAIN_NAME.match(name):
        raise ValueError(f"{var_name} should start with a letter and only contain letters, digits, '_' , and '-'")
    return name


class Chain:
    """
    Chain objects can be created and initialized globally (at module level) and used as functions,
    it chains the given functions and wraps them in nodes that capture any error and decide
    whether to continue or stop based one the result, and report the process statistics and failures.
    """
    __slots__ = '_name', '__core', '__get_reporter', '__len', 'namespace', 'handlers'

    def __init__(
            self,
            name: str,
            *chainables: CHAINABLES,
            log_failures: bool = True,
            log_statistics: bool = True,
            namespace: str | None = None,
            concatenate_namespace: bool = True,
    ) -> None:
        """
        chains required a name and a couple of functions
        in the correct order that will be chained, although
        it's possible to define structures using a dict or
        a list of functions.

        :param name: the name that identifies the chain (should be unique).
        :param chainables: function(Any)->Any, tuple of chainables, dict str -> chainables, list of chainables ...
        :param log_failures: whether to log failures with the standard logging.Logger or not, default to True.
        :param raise_for_fail: whether to raise an exception for failures from required nodes (default None).
        :type name: str
        :type chainables: function | tuple | dict | list ...
        :type log_failures: bool
        :type raise_for_fail: bool
        """
        validate_chain_name(name)
        if namespace is not None:
            validate_chain_name(namespace)
            if concatenate_namespace:
                name = f'{namespace}_{name}'
        self._name: str = name
        self.namespace: str | None = namespace
        core = parse(chainables)
        self.__core: Chainable = core
        self.__len: int = len(core)
        self.handlers: dict[str, list[tp.Callable]] = {}
        handlers = []
        if log_failures:
            handlers.append(LoggingHandler)
        self.__get_reporter: ReporterMaker = ReporterMaker(name, core, handlers)

    @tp.overload
    def add_handler(self, event: tp.Literal['statistics'], handler: tp.Callable[[ReportStatistics], None]) -> None: ...
    @tp.overload
    def dispatch(self, event: tp.Literal['statistics'], statistics: ReportStatistics): ...
    @tp.overload
    def add_handler(self, event: tp.Literal['failures'], handler: tp.Callable[[FailureDetails], None]) -> None: ...
    @tp.overload
    def dispatch(self, event: tp.Literal['failures'], failure: FailureDetails): ...

    def add_handler(self, event: str, handler: tp.Callable[..., None]) -> None:
        if not callable(handler):
            raise TypeError("handler must be a callable")
        if event in self.handlers:
            self.handlers[event].append(handler)
        else:
            self.handlers[event] = [handler, ]

    def dispatch(self, event: str, *args, **kwargs) -> None:
        for handler in self.handlers.get(event, ()):
            handler(*args, **kwargs)

    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        if self.namespace is not None:
            return f'{self.namespace}_{self._name}'
        return self._name

    def __repr__(self) -> str:
        """representation string of the chain"""
        return f'<chain {self._name!r}>'

    def __len__(self) -> int:
        """number of nodes the chain has"""
        return self.__len

    def __call__(self, input: tp.Any, reports: dict[str, dict] | None = None):
        """
        processes the given input and returns the result,
        the chain creates its reporter and only registers it
        if reports is not None.

        :param input: the entry data to be processed
        :param reports: a dictionary where to register the execution statistics.
        :type reports: dict[str, dict[str, Any]]
        :return: the result result from given input.
        """
        reporter = self.__get_reporter()
        result = self.__core.process(input, reporter)[1]
        if reports is not None:
            reports[self._name] = dict(**reporter.statistics(), errors=reporter.failures)
        return result


class ChainMaker:
    """Utility object for making a group of chains with the same configuration and same prefix."""
    __slots__ = 'name', 'log_failures', 'raise_for_fail', '__registered_chains__'

    def __init__(self, name: str, *, log_failures: bool = True):
        self.name: str = validate_chain_name(name)
        self.log_failures: bool = log_failures
        self.__registered_chains__: dict[str, Chain] = {}

    def __contains__(self, name: str) -> bool:
        return name in self.__registered_chains__

    def __getitem__(self, name: str) -> Chain:
        if not isinstance(name, str):
            raise TypeError("name must be str")
        try:
            return self.__registered_chains__[name]
        except KeyError:
            raise KeyError(f"no chain is registered with the name {name!r}")

    def __call__(self, name: str, *chainables: CHAINABLES) -> Chain:
        """
        creates a new chain with the same configuration and same prefix.

        :param name: the name of the new chain.
        :param chainables: the body of the new chain.
        :return: the new created chain.
        """
        if name in self:
            raise ValueError("a chain with the same name already been registered.")
        new_chain = Chain(name, *chainables, log_failures=self.log_failures, namespace=self.name)
        self.__registered_chains__[name] = new_chain
        return new_chain
