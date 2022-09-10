import itertools
import re
from operator import countOf
from typing import Any, Pattern, Callable, TypeAlias, Union, Literal
from .nodes import Node
from .factory import parse, NodeFactory
from .monitoring import Reporter, Report, print_report, failures_logger

ChainRegistry: TypeAlias = dict[str, Union['Chain', dict]]
ReportHandler: TypeAlias = Callable[[Report], None]
SupportedChainables: TypeAlias = Union[
    Callable[[Any], Any],
    tuple,
    dict,
    list,
    Literal['?', '*'],
    NodeFactory
]

_registry_: ChainRegistry = {}
VALID_NAME: Pattern[str] = re.compile(r'^[a-z](?:\w+[_-]?)*?$', re.IGNORECASE)


class Chain:
    __slots__ = ('__name',
                 '__core',
                 '__required_nodes',
                 '__total_nodes',
                 '__nodes',
                 '__report_handlers')

    def __init__(self, core: Node, name: str | None = None) -> None:
        """
        Initializes the new chain with a pre parsed core

        :param core: A Node or NodeGroup subclass instance
        :param name: An optional chain name (default 'unregistered')
        """
        nodes = core.expose
        self.__name: str = name if name is not None else 'unregistered'
        self.__core: Node = core
        self.__nodes: set = set(nodes)
        self.__total_nodes: int = len(nodes)
        self.__required_nodes: int = countOf(nodes.values(), True)
        self.__report_handlers: dict[bool, list[ReportHandler]] = {True: [], False: []}

    def add_report_handler(self, handler: ReportHandler, always: bool = False) -> None:
        """Adds a function to capture the execution report.

        :param handler: A callable that only takes the report dict as parameter.
        :param always: If True, the handler will always be called, otherwise,
                       It will only be called in case of failures.
        """
        if always:
            self.__report_handlers[True].append(handler)
        self.__report_handlers[False].append(handler)

    def clear_report_handlers(self) -> None:
        """Removes all the previously added handlers, including the default ones."""
        self.__report_handlers = {True: [], False: []}

    @property
    def name(self) -> str:
        """Gets the name of the chain (readonly)"""
        return self.__name

    def __repr__(self) -> str:
        """String representation of the chain"""
        return (f'{self.__class__.__name__}(name={self.__name!r}, '
                f'nodes/required={self.__total_nodes}/{self.__required_nodes})')

    def __len__(self) -> int:
        """Chain size in nodes"""
        return self.__total_nodes

    def __call__(self, input: Any) -> Any:
        """Processes the input through the chain's nodes and returns the result."""
        reporter = Reporter()
        success, result = self.__core(input, reporter)
        handlers = self.__report_handlers[success]
        if handlers:
            report = reporter.report(self.__nodes, self.__required_nodes)
            for handler in handlers:
                handler(report)
        return result


def _get_components(source: None | Chain | ChainRegistry) -> list[Chain]:
    """Gets all chains from the given registry"""
    if source is None:
        return []
    if isinstance(source, dict):
        return list(itertools.chain(*map(_get_components, source.values())))
    return [source]


def _register(names: list[str], chain: Chain) -> None:
    """Registers the chain to the main tree under the hierarchical list of names"""
    last = len(names) - 1
    reg = _registry_
    for pos, name_part in enumerate(names):
        if name_part not in reg:
            if pos == last:
                reg[name_part] = chain
                return
            reg[name_part] = {}
        if isinstance(reg[name_part], dict):
            reg = reg[name_part]
        else:
            raise ValueError(f"A component is already registered under the name {'.'.join(names[:pos + 1])!r}")


def get(name: str | None = None) -> list[Chain]:
    """Gets all the previously created chain by their dot-separated hierarchical name,
     or gets all the chains registered chains if no name is given."""
    if name is None:
        names = []
    elif isinstance(name, str):
        names = name.split('.')
    else:
        raise TypeError("The name must be str")
    target = _registry_
    for pos, name_part in enumerate(names):
        target = target.get(name_part)
        if not isinstance(target, dict) and pos < (len(names) - 1):
            return []
    return _get_components(target)


def make(
        *components: SupportedChainables,
        name: str | None = None,
        log_failures: bool = True,
        logger: str | None = 'fastchain',
        print_stats: bool = False,
        register: bool = True
        ) -> Chain:
    if name is None:
        register = False
    else:
        if not isinstance(name, str):
            raise TypeError("The name must be str")
        if not name:
            raise ValueError("The name cannot be empty")
        names = name.split('.')
        for name_part in names:
            if not VALID_NAME.match(name_part):
                raise ValueError(f"{name_part!r} is not a valid name")
    core = parse(components)
    core.set_title(name)
    chain = Chain(core, name)
    if log_failures:
        chain.add_report_handler(failures_logger(logger), True)
    if print_stats:
        chain.add_report_handler(print_report, True)
    if register:
        _register(names, chain)  # noqa
    return chain


def add_report_handler(name: str, handler: ReportHandler, always: bool = False) -> None:
    for chain in get(name):
        chain.add_report_handler(handler, always)


def clear_report_handlers(name: str) -> None:
    for chain in get(name):
        chain.clear_report_handlers()
