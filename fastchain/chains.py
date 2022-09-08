import re
from operator import countOf
from typing import Any, Pattern, Callable, TypeAlias
from .nodes import Node
from .factory import parse
from .monitoring import Reporter, Report, print_report, failures_logger


ChainRegistry: TypeAlias = dict[str, 'Chain' | dict]
ReportHandler: TypeAlias = Callable[[Report], None]

REGISTER: bool = True
_registry_: ChainRegistry = {}
NAME_PATTERN: Pattern[str] = re.compile(r'^[a-z](?:\w+[_-]?)*?$', re.IGNORECASE)


class Chain:
    __slots__ = ('__name',
                 '__core',
                 '__required_nodes',
                 '__total_nodes',
                 '__nodes',
                 '__get_reporter',
                 '__report_handlers')

    def __init__(self, name: str, core: Node, get_reporter: Callable[[], Reporter]) -> None:
        self.__name: str = name
        self.__core: Node = core
        nodes = core.expose
        self.__required_nodes: int = countOf(nodes.values(), True)
        self.__nodes: set = set(nodes)
        self.__total_nodes: int = len(nodes)
        self.__get_reporter: Callable[[], Reporter] = get_reporter
        self.__report_handlers: dict[bool, list[ReportHandler]] = {True: [], False: []}

    def add_report_handler(self, handler: ReportHandler, always: bool = False) -> None:
        if always:
            self.__report_handlers[True].append(handler)
        self.__report_handlers[False].append(handler)

    @property
    def name(self) -> str:
        """Gets the name of the chain (readonly)"""
        return self.__name

    def __repr__(self) -> str:
        """String that represents the chain"""
        return f'<chain {self.__name!r}>'

    def __len__(self) -> int:
        """Chain size in nodes"""
        return self.__total_nodes

    def __call__(self, input: Any) -> Any:
        reporter = self.__get_reporter()
        success, result = self.__core(input, reporter)
        handlers = self.__report_handlers[success]
        if handlers:
            report = reporter.report(self.__nodes, self.__required_nodes)
            for handler in handlers:
                handler(report)
        return result


def _split_name(name: str | None) -> list[str]:
    """Splits a dot-separated hierarchical name to a list of names"""
    if name is None:
        return []
    elif isinstance(name, str):
        return name.split('.')
    raise TypeError("The name must be string")


def _validate_names(names: list[str]) -> None:
    """Validates the chain hierarchical names"""
    if not names:
        raise ValueError("The name cannot be empty")
    for name_part in names:
        if NAME_PATTERN.match(name_part):
            continue
        raise ValueError(f"{name_part!r} is not a valid name, "
                         "it must start with a letter and only contain letters, digits _ or -")


def _get_by_name(names: list[str], registry: ChainRegistry) -> None | Chain | ChainRegistry:
    """Recursively gets items by names from registry"""
    for name_part in names:
        if not isinstance(registry, dict):
            return None
        registry = registry.get(name_part)
    return registry


def _get_registry_chains(registry: ChainRegistry) -> list[Chain]:
    """Gets all chains from the given registry"""
    chains = []
    for value in registry.values():
        if isinstance(value, dict):
            chains.extend(_get_registry_chains(value))
        elif isinstance(value, Chain):
            chains.append(value)
    return chains


def get(name: str | None = None) -> list[Chain]:
    """
    Gets the chain(s) registered under a given name

    :param name: A name or names separated by dots (default None)
    :type name: str | None
    :return: A list of chains
    :rtype: list[ChainBase]
    """
    result = _get_by_name(_split_name(name), _registry_)
    if isinstance(result, Chain):
        return [result]
    elif isinstance(result, dict):
        return _get_registry_chains(result)
    return []


def _register(name_parts: list[str], chain: Chain, registry: ChainRegistry) -> None:
    """registers the chain in __registry__ using name_part without checking"""
    *name_parts, last_part = name_parts
    previous_parts = []
    for name_part in name_parts:
        if name_part not in registry:
            registry[name_part] = dict()
        elif isinstance(registry[name_part], Chain):
            name = '.'.join(previous_parts)
            raise ValueError(f"A chain with the name {name!r} is already registered")
        previous_parts.append(name_part)
        registry = registry[name_part]
    registry[last_part] = chain


def make(
        name: str,
        *components,
        log_failures: bool = True,
        logger: str | None = 'fastchain',
        print_stats: bool = False,
        register: bool = True
) -> Chain:
    # name validation
    names = _split_name(name)
    _validate_names(names)

    # ensuring uniqueness
    result = _get_by_name(names, _registry_)
    if result is not None:
        if isinstance(result, Chain):
            raise ValueError(f"A chain with the name {name!r} has already been created")
        chain_number = len(_get_registry_chains(_registry_))
        raise ValueError(f"A group of {chain_number} chains is registered under the name {name!r}")
    del result

    # parsing components and creating the chain
    core = parse(components, name)
    chain = Chain(name, core, Reporter)

    # registering report handlers
    if log_failures:
        chain.add_report_handler(failures_logger(logger), True)
    if print_stats:
        chain.add_report_handler(print_report, True)

    # registering and returning the chain
    if REGISTER and register:
        _register(names, chain, _registry_)
    return chain
