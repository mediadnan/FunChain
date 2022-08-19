"""
This module implements the chain object class,
the main object used to define data processing pipelines.
and ChainGroup a factory that produces chains
needed to be grouped and controlled together.

Chain and ChainGroup can be directly imported from fastchain.
"""
import re
import typing as tp

from ._abc import ReportDetails
from .chainables import Chainable
from .factory import CHAINABLES, parse
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
    Chain objects can be created and initialized globally (at module level) and used as functions,
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

    def __init__(self, name: str, *chainables: CHAINABLES, **kwargs) -> None:
        """
        chains required a name and a couple of functions
        in the correct order that will be chained, although
        it's possible to define structures using a dict or
        a list of functions.

        {chain_args}
        {chain_keywords}
        """
        validate_name(name)
        if 'namespace' in kwargs:
            namespace = validate_name(kwargs['namespace'], 'namespace')
            if kwargs.get('concatenate_namespace', True):
                name = f'{namespace}_{name}'
        self.__name = name
        self.__core = parse(chainables)
        self.__len = len(self.__core)
        self.__report_handler = {True: [], False: []}
        if kwargs.get('log_failures', True):
            logging_handler = LoggingHandler(kwargs.get('logger'), kwargs.get('print_stats', True))
            self.add_report_handler(logging_handler.handle_report)
        self.__get_reporter = ReporterMaker(self.__core)

    def add_report_handler(
            self,
            handler: tp.Callable[[ReportDetails], None],
            event: tp.Literal['failed_only', 'always'] = 'always'
    ) -> None:
        """
        registers the handler to the chain

        {report_details}
        """
        if event == 'always':
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
        """number of nodes the chain has"""
        return self.__len

    def __call__(self, input):
        """
        processes the given input and returns the result,
        the chain creates its reporter and only registers it
        if reports is not None.
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
    __slots__ = '__name', '__kwargs', '__registered_chains__'

    def __init__(self, name: str, **kwargs):
        """
        initializes the new chain group object with a name and configuration

        :param name: the group name that identifies a collection of chains
        {chain_keywords}
        """
        self.__name: str = validate_name(name)
        self.__kwargs: dict[str, tp.Any] = kwargs
        self.__registered_chains__: dict[str, Chain] = {}

    def name(self) -> str:
        """gets the name of the chain group - readonly"""
        return self.__name

    def add_report_handler(
            self,
            handler: tp.Callable[[ReportDetails], None],
            event: tp.Literal['failed_only', 'always'] = 'always'
    ) -> None:
        """
        registers the handler to every chain of this group

        {report_details}
        """
        for chain in self.__registered_chains__.values():
            chain.add_report_handler(handler, event)

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
        Chain.add_report_handler,
        ChainGroup.__init__,
        ChainGroup.__call__,
        ChainGroup.add_report_handler,
):
    method.__doc__ = method.__doc__.format_map({
        'chain_args': """:param name: name that identifies the chain (should be unique)
        :param chainables: a callable any chainable object""",
        'chain_keywords': """:keyword namespace: name of the chain's group name (default None)
        :keyword concatenate_namespace: if True the chain's name will be <namespace>_<name> else <name> (default True)
        :keyword logger: a custom logger to be used in logging (default logger('fastchain'))
        :keyword log_failures: whether to log failed with standard logging (default True)
        :keyword print_stats: whether to print statistics at the end of each call""",
        'report_details': """report handlers will be called with a report (dict)
        containing the following information;
        
        **rate** *(float)*
            represents a ratio (between 0.0 and 1.0) of successful operations over the total.
        
        **succeeded** *(int)*
            number of successful operations (from different or same nodes).
            
        **failed** *(int)*
            number of unsuccessful operations (from different or same nodes).
        
        **missed** *(int)*
            number of unreached nodes.
            
        **required** *(int)*
            number of non optional nodes from non optional branches.
            
        **total** *(int)*
            number of nodes in total.
        
        **failed** *(list[dict])*
            list for registered failed with the following details:
                + source (str): the title of the failing component.
                + input (Any): the value that caused the failure.
                + error (Exception): the error raised causing the failure.
                + fatal (bool): True if the component is not optional. 
        
        :param handler: function that only takes the report dict
        :type handler: (ReportDetails) -> None
        :param event: 'failed_only' to triggered the handler only when the chain process fails or 
                      'always' (default 'always')
        :type event: str
        :return: None
        """
    })
