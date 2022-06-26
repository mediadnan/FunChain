import logging
import warnings
from weakref import WeakValueDictionary
from typing import (
    Union,
    Dict,
    Tuple,
    Any,
    Optional,
    Type,
    Literal,
)

from .elements import ChainableNode, ChainOption, ChainMapOption, ChainFunc, ChainGroup, ChainModel
from .wrapper import Wrapper, CHAINABLE_FUNC
from .reporter import Reporter, REPORT_CALLBACK
from .tools import validate

# type aliases
SUPPORTED_CHAINABLE_OBJECTS = Union[            # type: ignore
    Wrapper,
    CHAINABLE_FUNC,
    Literal['*'],
    Dict[str, 'SUPPORTED_CHAINABLE_OBJECTS'],   # type: ignore
    Tuple['SUPPORTED_CHAINABLE_OBJECTS', ...]   # type: ignore
]
CHAIN_OPTIONS: Dict[str, Type[ChainOption]] = {
    '*': ChainMapOption,
}


class Chain:
    __doc__ = """
    Chain objects are callables that take a single argument and pass it to the internal
    structure initially parsed then returns the value or default in case of failure.

    if a callback function is passed when initializing, this callback will be called
    at the end of the execution with the report object holding information about
    the execution and failures.

    if log is True, the errors will be logged with the standard logging module.

    the title of each chain should be unique to avoid confusion when receiving reports.
    """

    __title: str
    __core: ChainableNode
    __len: int
    __logger: Optional[logging.Logger] = None
    __callback: Optional[REPORT_CALLBACK] = None
    __reporter: Reporter

    __chains: WeakValueDictionary = WeakValueDictionary()

    def __new__(
            cls,
            *chainables: SUPPORTED_CHAINABLE_OBJECTS,
            title: str,
            callback: REPORT_CALLBACK = None,
            log: bool = False,
    ):
        if title in cls.__chains:
            warnings.warn(f"a chain with the title {title!r} already exists!", UserWarning, stacklevel=2)
        chain = super().__new__(cls)
        cls.__chains[title] = chain
        return chain

    def __init__(
            self,
            *chainables: SUPPORTED_CHAINABLE_OBJECTS,
            title: str,
            callback: REPORT_CALLBACK = None,
            log: bool = False,
    ) -> None:
        """
        prepares the chain by parsing supported chainable objects.

        :param chainables: supported chainable objects,
        :param title: a unique title that identifies the chain.
        :param callback: a function that takes a Report object at the end of execution. (optional, default: None)
        :param log: if True, the errors are logged with standard logging module. (optional, default: False)
        """
        self.__core = parse(title, chainables)
        self.__title = title
        self.__len = len(self.__core)
        self.__reporter = Reporter(title, len(self.__core))
        if callback:
            self.__callback = callback
        if log:
            self.__logger = logging.getLogger(self.title)

    @property
    def title(self) -> str:
        """gets the name of the chain - read-only"""
        return self.__title

    @property
    def core(self) -> ChainableNode:
        """gets the chain structure object - read-only"""
        return self.__core

    @classmethod
    def chains(cls) -> WeakValueDictionary:
        return cls.__chains

    def __repr__(self) -> str:
        return f'<Chain {self.title!r}: {self.core!r}>'

    def __len__(self) -> int:
        return self.__len

    def __call__(self, arg: Any) -> Any:
        _, result = self.__core(arg, self.__reporter, self.__logger)
        if self.__callback:
            self.__callback(self.__reporter.report())
            self.__reporter.reset()
        return result


def parse(title: str, structure: SUPPORTED_CHAINABLE_OBJECTS) -> ChainableNode:
    """converts the model structure into a chain structure"""
    return _parse(validate(title, 'title', str, True), structure)


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
