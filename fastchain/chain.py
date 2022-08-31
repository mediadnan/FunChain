"""
This module implements the Chain class, the main class
used by FastChain users to define data processing pipelines
and use them as regular functions.

The module also implements a ChainGroup class
for chain-group objects for chains that are related
or considered in the same category and share
configuration.

Chain and ChainGroup can be directly imported from fastchain.
"""
import re
import typing as tp

from ._abc import ReportDetails
from .chainables import Chainable
from .factory import parse
from .monitoring import LoggingHandler, ReporterMaker

T = tp.TypeVar('T')
CHAIN_NAME: tp.Pattern[str] = re.compile(r'^[a-z_](?:\w+[_-]?)+?$', re.IGNORECASE)


def validate_name(name: str, var_name: str = 'name') -> str:
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
    The chain is created globally (at module level) and used as regular functions,
    it takes a name and a structure (functions usually) that will be called
    sequentially (or simultaneously also) depending on the defined structure.

    The chain can store any number of report handlers, those are functions that take
    a dictionary containing execution details, and do with that whatever needed.

    it chains the given functions and wraps them in nodes that capture any error and decide
    whether to continue or stop based one the result, and report the process statistics and failed.
    """
    __name: str
    __core: Chainable
    __len: int
    __get_reporter: ReporterMaker
    __report_handler: dict[bool, list[tp.Callable[[ReportDetails], None]]]

    __slots__ = ('__name',
                 '__core',
                 '__len',
                 '__get_reporter',
                 '__report_handler')

    def __init__(self, name: str, *chainables, **kwargs) -> None:
        """
        a chain is defined with a name and a body from a given structure, supported chainables objects for the body are:

        + functions (or any callables), multiple functions (or tuple of functions) will be composed (f3(f2(f1(arg))))
        + functions wrapped with chainable or from a funfact (check chainable and funfact documentation)
        + dictionary of functions will return a dictionary of the same keys mapped to results
        + list of functions will return a list of results
        + match(func1, func2, ...) applied to an iterable (arg1, arg2, ...) will return (func1(arg1), func2(arg2), ...)
        + option characters ('*' or '?') are placed before functions, '*' for iteration and '?' to make nodes optional

        all the structures listed above could be nested as deep as needed

        :param name: name that identifies the chain (should be unique)
        :type name: str
        :param chainables: a callable or any supported structure
        :keyword namespace: name of the chain's group name (default None)
        :keyword logger: a custom logger to be used in logging (default logger('fastchain'))
        :keyword log_failures: whether to log failed with standard logging (default True)
        :keyword print_stats: whether to print statistics at the end of each call
        """
        validate_name(name)
        if 'namespace' in kwargs:
            namespace = validate_name(kwargs['namespace'], 'namespace')
            if kwargs.get('concatenate_namespace', True):
                name = f'{namespace}::{name}'
        self.__name = name
        self.__core = parse(chainables, name)
        self.__len = len(self.__core)
        self.__report_handler = {True: [], False: []}
        if kwargs.get('log_failures', True):
            logging_handler = LoggingHandler(kwargs.get('logger'), kwargs.get('print_stats', False))
            self.add_report_handler(logging_handler.handle_report, True)
        self.__get_reporter = ReporterMaker(self.__core)

    def add_report_handler(self, handler: tp.Callable[[ReportDetails], None], always: bool = False) -> None:
        """
        adds the given report handler to the chain,
        it will be called after the execution with a report *(dict)* containing the following info:

        + **rate** *(float)*: represents a ratio (between 0.0 and 1.0) of successful operations over the total.
        + **succeeded** *(int)*: number of successful operations (from different or same nodes).
        + **failed** *(int)*: number of unsuccessful operations (from different or same nodes).
        + **missed** *(int)*: number of unreached nodes.
        + **required** *(int)*: number of non optional nodes from non optional branches.
        + **total** *(int)*: number of nodes in total.
        + **failed** *(list[dict])*: list for registered failed with the following details:

            + **source** *(str)*: the title of the failing component.
            + **input** *(Any)*: the value that caused the failure.
            + **error** *(Exception)*: the error raised causing the failure.
            + **fatal** *(bool)*: True if the component is not optional.

        :param handler: function that takes the report dict (only)
        :type handler: Callable[[ReportDetails], None]
        :param always: if False, the handler will be triggered only when the chain fails, otherwise
                      it will always be triggered (default False)
        :type always: bool
        :return: None
        """
        if always:
            self.__report_handler[True].append(handler)
        self.__report_handler[False].append(handler)

    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        return self.__name

    def __repr__(self) -> str:
        """representation string of the chain"""
        return f'<chain {self.__name!r}>'

    def __len__(self) -> int:
        """chain size is the number of nodes it contains"""
        return self.__len

    def __call__(self, input: tp.Any) -> tp.Any:
        """
        processes the given input through its internal nodes defined when the chain was created

        :param input: the initial data to be processed, it will be passed to the first function
        :returns: the output of the last function
        """
        reporter = self.__get_reporter()
        success, result = self.__core.process(input, reporter)
        handlers = self.__report_handler[success]
        if handlers:
            report = reporter.report()
            for handler in handlers:
                handler(report)
        return result


class ChainGroup:
    """utility object for making a group of chains with the same configuration and name prefix"""
    __slots__ = '__name', '__kwargs', '__prefix', '__registered_chains__'

    def __init__(self, name: str, *, prefix: bool = True, **kwargs):
        """
        new chain groups are defined with a name and optionally common chain configurations

        :param name: name that identifies a group of chains
        :type name: str
        :param prefix: if True the chain's name will be <namespace>::<name> else <name> (default True)
        :type prefix: bool
        :keyword log_failures: whether to log failed with standard logging (default True)
        :keyword logger: custom logger to be used in logging (default logger('fastchain'))
        :keyword print_stats: whether to print statistics at the end of each call
        """
        self.__name: str = validate_name(name)
        self.__prefix: bool = prefix
        self.__kwargs: dict[str, tp.Any] = kwargs
        self.__registered_chains__: dict[str, Chain] = {}

    @property
    def name(self) -> str:
        """gets the name of the chain group - readonly"""
        return self.__name

    def add_report_handler(self, handler: tp.Callable[[ReportDetails], None], always: bool = False) -> None:
        """
        registers the report handler to every chain of this group,
        for more details try help(Chain.add_report_handler)

        :param handler: function that only takes the report dict
        :type handler: (ReportDetails) -> None
        :param always: if False, the handler will be triggered only when the chain fails, otherwise
                      it will always be triggered (default False)
        :type always: bool
        :return: None
        """
        for chain in self.__registered_chains__.values():
            chain.add_report_handler(handler, always)

    def __contains__(self, name: str | Chain) -> bool:
        return name in self.__registered_chains__

    def __getitem__(self, name: str) -> Chain:
        try:
            return self.__registered_chains__[name]
        except KeyError:
            raise KeyError(f"no chain is registered with the name {name!r}")

    def __call__(self, name: str, *chainables, **kwargs) -> Chain:
        """
        creates and registers a new chain and merges the newly defined
        configuration to the previously defined.

        :param name: name that identifies the chain (should be unique)
        :param chainables: a callable or any supported structure
        :keyword namespace: name of the chain's group name (default None)
        :keyword logger: a custom logger to be used in logging (default logger('fastchain'))
        :keyword log_failures: whether to log failed with standard logging (default True)
        :keyword print_stats: whether to print statistics at the end of each call
        :raises ValueError: when trying to create a chain with a same name as a previously registered chain
        :return: new chain
        :rtype: Chain
        """
        if name in self:
            raise ValueError("a chain with the same name already been registered.")
        kwargs.update(self.__kwargs)
        if self.__prefix:
            kwargs['namespace'] = self.name
        new_chain = Chain(name, *chainables, **kwargs)
        self.__registered_chains__[name] = new_chain
        return new_chain
