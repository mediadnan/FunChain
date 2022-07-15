import re
from types import MappingProxyType
from weakref import WeakValueDictionary as WeakDict
from typing import TypeAlias, Any, Callable, Pattern, overload
from copy import copy

from .elements import CHAINABLE, Chainable, T2, T1, ChainNode, ChainSequence
from .customization import PreChainable
from .reporter import ReportStats, Reporter


# type aliases
CHAINABLES: TypeAlias = CHAINABLE | PreChainable | dict[str | int, Any] | tuple | list | str
REPORT_CALLBACK: TypeAlias = Callable[[ReportStats], None]
# constants
CHAIN_NAME: Pattern[str] = re.compile(r'^\w[\w\d_-]*?$', re.DOTALL)


class Chain:
    __chains__: WeakDict[str, 'Chain'] = WeakDict()
    __slots__ = (
        '__weakref__',
        '__name',
        '__core',
        '__required_nodes'
    )

    def __init__(self, name: str, *chainables: CHAINABLES):
        if not isinstance(name, str):
            raise TypeError("the name of the chain must be a string.")
        elif CHAIN_NAME.match(name):
            raise ValueError("chain's name must begin with a letter and only contain letter, digits, _ and -")
        elif name in self.__chains__:
            raise ValueError("a chain with the same name already exists.")
        self.__name: str = name
        self.__core: Chainable = parse(chainables)
        self.__required_nodes: list[Chainable] = []
        self.__core.register_required(self.__required_nodes)

    @overload
    def parse(self, obj: Callable[[T1], T2]) -> ChainNode[T1, T2]: ...
    @overload
    def parse(self, obj: tuple[CHAINABLES, ...]) -> ChainSequence[T1, T2]: ...
    @overload
    def parse(self, obj: Callable[[T1], T2]) -> ChainNode[T1, T2]: ...
    @overload
    def parse(self, obj: Callable[[T1], T2]) -> ChainNode[T1, T2]: ...
    @overload
    def parse(self, obj: Callable[[T1], T2]) -> ChainNode[T1, T2]: ...

    def parse(self, obj: CHAINABLES) -> Chainable:
        if callable(obj):
            ...
        elif isinstance(obj, tuple):
            ...
        elif isinstance(obj, dict):
            ...
        elif isinstance(obj, list):
            ...
        else:
            raise TypeError(f"unchainable type {type(obj)}")


    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        return self.__name

    @property
    def core(self) -> Chainable:
        """gets the chain internal structure - readonly"""
        return self.__core

    @classmethod
    def chains(cls) -> MappingProxyType[str, 'Chain']:
        """gets a immutable mapping of registered chains - readonly"""
        return MappingProxyType(cls.__chains__)

    def __repr__(self) -> str:
        return f'<Chain {self.name!r}: {self.core!r}>'

    def __call__(self, arg: Any, reporter: Reporter | None = None) -> Any:
        if reporter is None:
            reporter = Reporter(self.__required_nodes, self.__name)
        else:
            reporter.add_components(self.__required_nodes)
        return self.__core(arg, reporter)[1]


def parse(obj: CHAINABLES) -> Chainable:
    """converts the model structure into a chain structure"""
    if isinstance(obj, Chainable):
        return copy(obj)

    elif callable(obj):
        return _parse(title, Wrapper(obj))

    elif isinstance(obj, str):
        try:
            return CHAIN_OPTIONS[obj](title)
        except KeyError:
            options = ', '.join(map(repr, CHAIN_OPTIONS.keys()))
            raise ValueError(f"unrecognized option {obj!r}, available options are: {options}")

    elif isinstance(obj, tuple):
        if len(obj) == 1:
            return _parse(title, obj[0])
        return ChainGroup(
            tuple(_parse(title, element) for element in obj),
            title
        )

    elif isinstance(obj, dict):
        return ChainModel(
            {
                key: _parse(f"{title} / {key}", member)
                for key, member in obj.items()
            },
            title
        )

    else:
        raise ValueError(f"unsupported type '{type(obj).__name__}' cannot be parsed.")


def _parse(title: str, obj: SUPPORTED_CHAINABLE_OBJECTS) -> ChainableNode:
    if isinstance(obj, Wrapper):
        return ChainFunc(obj, title)

    elif callable(obj):
        return _parse(title, Wrapper(obj))

    elif isinstance(obj, str):
        try:
            return CHAIN_OPTIONS[obj](title)
        except KeyError:
            options = ', '.join(map(repr, CHAIN_OPTIONS.keys()))
            raise ValueError(f"unrecognized option {obj!r}, available options are: {options}")

    elif isinstance(obj, tuple):
        if len(obj) == 1:
            return _parse(title, obj[0])
        return ChainGroup(
            tuple(_parse(title, element) for element in obj),
            title
        )

    elif isinstance(obj, dict):
        return ChainModel(
            {
                key: _parse(f"{title} / {key}", member)
                for key, member in obj.items()
            },
            title
        )

    else:
        raise ValueError(f"unsupported type '{type(obj).__name__}' cannot be parsed.")
