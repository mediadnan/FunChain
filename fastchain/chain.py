"""
This module implements the chain object class,
the main object used to define data processing pipelines.
and ChainMaker a factory that produces chains
needed to be grouped and controlled together.

Chain and ChainMaker can be directly imported from fastchain.
"""
import enum
import re
import logging
import functools
import typing as tp

from .chainables import Chainable
from .factory import CHAINABLES, parse
from .monitoring import ReporterMaker, ReportStatistics, FailureDetails
from .handlers import logger as logging_handler

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


class Event(enum.Enum):
    failures: 'failures'
    statistics: 'statistics'


class Chain:
    """
    Chain objects can be created and initialized globally (at module level) and used as functions,
    it chains the given functions and wraps them in nodes that capture any error and decide
    whether to continue or stop based one the result, and report the process statistics and failures.
    """
    __slots__ = '__name', '__core', '__get_reporter', '__len', '__handlers'

    def __init__(self, name: str, *chainables: CHAINABLES, **kwargs) -> None:
        """
        chains required a name and a couple of functions
        in the correct order that will be chained, although
        it's possible to define structures using a dict or
        a list of functions.

        {chain_args}
        {chain_keywords}
        """
        validate_chain_name(name)
        if 'namespace' in kwargs:
            namespace = validate_chain_name(namespace, 'namespace')
            if kwargs.get('concatenate_namespace', True):
                name = f'{namespace}_{name}'
        self.__name: str = name
        self.__core: Chainable = parse(chainables)
        self.__len: int = len(self.__core)
        self.__handlers: dict[str, list[tp.Callable]] = {}
        for event, use_log_handler, logger, default, handler in (
            (Event.failures, 'log_failures', 'failures_logger', True, logging_handler.handle_failure),
            (Event.statistics, 'log_statistics', 'statistics_logger', True, logging_handler.handle_stats)
        ):
            if kwargs.get(use_log_handler, default):
                if logger in kwargs:
                    if not isinstance(logger, logging.Logger):
                        raise TypeError(f'logger must be an instance of {logging.Logger}')
                    handler = functools.partial(handler, logger=logger)
                self._add_handler(event, handler)
        self.__get_reporter: ReporterMaker = ReporterMaker(self.__core)

    def add_failures_handler(self, handler: tp.Callable[[tp.Iterable[FailureDetails]], None]): 
        self._add_handler(Event.failures, handler)

    def add_statistics_handler(self, handler: tp.Callable[[tp.Iterable[ReportStatistics]], None]):
        self._add_handler(Event.statistics, handler)

    def _add_handler(self, event: Event, handler: tp.Callable[..., None]) -> None:
        """subscribes an event handler to a specific event"""
        if not callable(handler):
            raise TypeError("handler must be a callable")
        if event in self.__handlers:
            self.__handlers[event].append(handler)
        else:
            self.__handlers[event] = [handler, ]

    def _dispatch(self, event: Event, *args, **kwargs) -> None:
        """calls a series of handlers subscribed the event with the given arguments"""
        for handler in self.__handlers.get(event, ()):
            handler(*args, **kwargs)

    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        self.__name

    def __repr__(self) -> str:
        """representation string of the chain"""
        return f'<chain {self.__name!r}>'

    def __len__(self) -> int:
        """number of nodes the chain has"""
        return self.__len

    def __call__(self, input: tp.Any):
        """
        processes the given input and returns the result,
        the chain creates its reporter and only registers it
        if reports is not None.

        :param input: the entry data to be processed
        :return: the result result from given input.
        """
        reporter = self.__get_reporter()
        result = self.__core.process(input, reporter)[1]
        if self.__handlers.get(Event.statistics, None):
            self._dispatch(Event.statistics, reporter.statistics())
        if self.__handlers.get(Event.failures, None) and reporter._failures:
            self._dispatch(Event.failures, reporter._failures)
        return result


class ChainMaker:
    """Utility object for making a group of chains with the same configuration and same prefix."""
    __slots__ = '__name', '__kwargs', '__registered_chains__'

    def __init__(self, name: str, **kwargs):
        """

        :param name: the group name that identifies a collection of chains
        {chain_keywords}
        """
        self.__name: str = validate_chain_name(name)
        self.__kwargs: dict[str, tp.Any] = kwargs
        self.__registered_chains__: dict[str, Chain] = {}

    def name(self) -> str:
        """gets the name of the chain-group - readonly"""
        return self.__name

    def __contains__(self, name: str) -> bool:
        return name in self.__registered_chains__

    def __getitem__(self, name: str) -> Chain:
        if not isinstance(name, str):
            raise TypeError("name must be str")
        try:
            return self.__registered_chains__[name]
        except KeyError:
            raise KeyError(f"no chain is registered with the name {name!r}")

    def __call__(self, name: str, *chainables: CHAINABLES, **kwargs) -> Chain:
        """
        creates and registers a new chain and merges the newly defined
        configuration to the previously defined.

        {chain_args}
        {chain_keywords}
        :raises ValueError: when trying to create a chain with a same name as a previously registered chain
        :return: new chain
        :rtype: Chain
        """
        if name in self:
            raise ValueError("a chain with the same name already been registered.")
        kwargs.update(self.__kwargs)
        new_chain = Chain(name, *chainables, **kwargs)
        self.__registered_chains__[name] = new_chain
        return new_chain


# update docs
 
for method in (
    Chain.__init__,
    ChainMaker.__init__,
    ChainMaker.__call__,
):
    method.__doc__ = method.__doc__.format_map({
        'chain_args': """:param name: name that identifies the chain (should be unique)
        :param chainables: a callable any chainable object""",
        'chain_keywords': """:keyword namespace: name of the chain's group name (default None)
        :keyword concatenate_namespace: if True the chain's name will be <namespace>_<name> else <name> (default True)
        :keyword log_failures: whether to log failures with standard logging (default True)
        :keyword failures_logger: custom logger to handle logging failures (default fastchain_logger)
        :keyword log_statistics: whether to log statistics with standard logging (default True)
        :keyword statistics_logger: custom logger to handle logging statistics (default fastchain_logger)"""
    })
