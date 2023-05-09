"""
The module defines different types of funchain nodes,
nodes are built and used by funchain chains
to perform the data processing.
"""
import functools
from abc import ABC, abstractmethod, ABCMeta
import asyncio
from typing import (
    Any,
    Self,
    Callable,
    Iterable,
    Coroutine,
    TypeAlias,
    TypeVar,
    Generic,
    Union,
    overload,
)
from failures import Reporter

from .util.name import get_func_name, guess_var_name, validate
from .util.tool import is_async, asyncify

Input = TypeVar('Input')
Output = TypeVar('Output')
Output2 = TypeVar('Output2')

AsyncCallable: TypeAlias = Callable[[Input], Coroutine[None, None, Output]]
Chainable: TypeAlias = Union[
    'BaseNode[Input, Output]',
    Callable[[Input], Output],
    'DictGroupChainable[Input]',
    'ListGroupChainable[Input]'
]
AsyncChainable: TypeAlias = Union[
    'AsyncBaseNode[Input, Output]',
    AsyncCallable[Input, Output],
    'AsyncDictGroupChainable[Input]',
    'AsyncListGroupChainable[Input]'
]
DictGroupChainable: TypeAlias = dict[Any, Chainable[Input, Any]]
ListGroupChainable: TypeAlias = list[Chainable[Input, Any]]
AsyncDictGroupChainable: TypeAlias = dict[Any, AsyncChainable[Input, Any] | Chainable[Input, Any]]
AsyncListGroupChainable: TypeAlias = list[AsyncChainable[Input, Any] | Chainable[Input, Any]]


class Severity(IntEnum):
    """
    Defines different levels of severity, each one for a different failure reaction

    OPTIONAL
        Basically indicates that the failure should be ignored

    NORMAL
        Indicates that the failure should be reported but without failure

    REQUIRED
        Indicates that the failure should be handled and the process should stop
    """
    OPTIONAL = 0
    NORMAL = 1
    REQUIRED = 2


# severity shortcuts
OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED


class BaseNode(ABC, Generic[Input, Output]):
    """Base class for all funchain nodes"""
    __slots__ = 'severity',
    severity: Severity

    def __init__(self) -> None:
        self.severity = Severity.NORMAL

    @overload
    def __or__(self, other: 'AsyncBaseNode[Output, Output2]') -> 'AsyncChain[Input, Output2]': ...
    @overload
    def __or__(self, other: 'BaseNode[Output, Output2]') -> 'Chain[Input, Output2]': ...
    @overload
    def __or__(self, other: AsyncCallable[Output, Output2]) -> 'AsyncChain[Input, Output2]': ...
    @overload
    def __or__(self, other: Callable[[Output], Output2]) -> 'Chain[Input, Output2]': ...
    @overload
    def __or__(self, other: AsyncDictGroupChainable[Output]) -> 'AsyncChain[Input, dict]': ...
    @overload
    def __or__(self, other: DictGroupChainable[Output]) -> 'Chain[Input, dict]': ...
    @overload
    def __or__(self, other: AsyncListGroupChainable[Output]) -> 'AsyncChain[Input, list]': ...
    @overload
    def __or__(self, other: ListGroupChainable[Output]) -> 'Chain[Input, list]': ...
    @overload
    def __mul__(self, other: 'AsyncBaseNode[Output, Output2]') -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: 'BaseNode[Output, Output2]') -> 'Chain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: AsyncCallable[Output, Output2]) -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: Callable[[Output], Output2]) -> 'Chain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: AsyncDictGroupChainable[Output]) -> 'AsyncChain[Input, list[dict]]': ...
    @overload
    def __mul__(self, other: DictGroupChainable[Output]) -> 'Chain[Input, list[dict]]': ...
    @overload
    def __mul__(self, other: AsyncListGroupChainable[Output]) -> 'AsyncChain[Input, list[list]]': ...
    @overload
    def __mul__(self, other: ListGroupChainable[Output]) -> 'Chain[Input, list[list]]': ...

    def __or__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain(self) | other

    def __mul__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain(self) * other

    @abstractmethod
    def __len__(self) -> int: ...

    def __repr__(self) -> str:
        return f"funchain.{self.__class__.__name__}({self.__len__()})"

    def __call__(
            self,
            arg, /, *,
            name: str | None = None,
            handler: Callable[[Failure], None] | None = FailureLogger()
    ) -> Output | None:
        """Processes arg and returns the result"""
        if name is None:
            name = guess_var_name()
        else:
            validate(name)
        return self.process(arg, Reporter(name, handler))

    def optional(self) -> Self:
        new = self.copy()
        new.severity = Severity.OPTIONAL
        return new

    def required(self) -> Self:
        new = self.copy()
        new.severity = Severity.REQUIRED
        return new

    @abstractmethod
    def process(self, arg, reporter: Reporter) -> Output | None: ...

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        """Returns an async version of the current node"""


class AsyncBaseNode(BaseNode[Input, Coroutine[None, None, Output]], Generic[Input, Output]):
    @overload
    def __or__(self, other: 'BaseNode[Output, Output2]') -> 'AsyncChain[Input, Output2]': ...
    @overload
    def __or__(self, other: Callable[[Output], Output2]) -> 'AsyncChain[Input, Output2]': ...
    @overload
    def __or__(self, other: DictGroupChainable[Output]) -> 'AsyncChain[Input, dict]': ...
    @overload
    def __or__(self, other: ListGroupChainable[Output]) -> 'AsyncChain[Input, list]': ...
    @overload
    def __mul__(self, other: 'BaseNode[Output, Output2]') -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: Callable[[Output], Output2]) -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: DictGroupChainable[Output]) -> 'AsyncChain[Input, list[dict]]': ...
    @overload
    def __mul__(self, other: ListGroupChainable[Output]) -> 'AsyncChain[Input, list[list]]': ...

    def __or__(self, other):
        return AsyncChain(self) | other

    def __mul__(self, other):
        return AsyncChain(self) * other

    def to_async(self) -> Self:
        """Returns the current node"""
        return self

    @abstractmethod
    async def process(self, arg, reporter: Reporter) -> Output | None: ...


class Node(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = 'func', 'name'
    name: str
    func: Callable[[Input], Output]

    def __init__(self, func: Callable[[Input], Output], name: str | None = None) -> None:
        super().__init__()
        self.func = func
        self.name = name or get_func_name(func)

    def __len__(self) -> int:
        return 1

    def copy(self) -> Self:
        return self.__class__(self.func, self.name)

    def to_async(self) -> 'AsyncNode[Input, Output]':
        return AsyncNode(asyncify(self.func), self.name)

    def named(self, name: str) -> Self:
        validate(name)
        new = self.copy()
        new.name = name
        return new

    def partial(self, *args, **kwargs) -> Self:
        func = self.func
        while isinstance(func, functools.partial):
            args = *func.args, *args
            kwargs = {**func.keywords, **kwargs}
            func = func.func
        self.func = functools.partial(func, *args, **kwargs)
        return self

    def process(self, arg: Input, reporter: Reporter) -> Output | None:
        with reporter(self.name, severity=self.severity, input=arg):
            return self.func(arg)


class AsyncNode(Node[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    func: Callable[[Input], Coroutine[None, None, Output]]

    async def process(self, arg: Input, reporter: Reporter) -> Output | None:
        with reporter(self.name, severity=self.severity, input=arg):
            return await self.func(arg)


class Chain(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = 'nodes', '__len'
    __len: int
    nodes: list[BaseNode]

    def __init__(self, *nodes: BaseNode) -> None:
        super().__init__()
        self.nodes = list(nodes)
        self.__len = sum(map(len, nodes)) if nodes else 0

    def __or__(self, other):
        if is_node_async(other):
            return self.to_async() | other
        nxt = build(other)
        return Chain(*self.nodes, nxt) if nxt else self.copy()

    def __mul__(self, other):
        if is_node_async(other):
            return self.to_async() * other
        nxt = build(other)
        return Chain(*self.nodes, Loop(nxt)) if nxt else self.copy()

    def __len__(self) -> int:
        return self.__len

    def copy(self) -> Self:
        return self.__class__(*(node.copy() for node in self.nodes))

    def to_async(self) -> 'AsyncChain[Input, Output]':
        return AsyncChain(*(node.to_async() for node in self.nodes))

    def process(self, arg, reporter: Reporter) -> Any | None:
        for index, node in enumerate(self.nodes):
            res = node.process(arg, reporter(f'c[{index}]'))
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(Chain[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    def __or__(self, other):
        nxt = async_build(other)
        return AsyncChain(*self.nodes, nxt) if nxt else self.copy()

    def __mul__(self, other):
        nxt = async_build(other)
        return AsyncChain(*self.nodes, AsyncLoop(nxt)) if nxt else self.copy()

    async def process(self, arg, reporter: Reporter) -> Any:
        for index, node in enumerate(self.nodes):
            res = await node.process(arg, reporter(f'c[{index}]'))
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class Loop(BaseNode[Iterable[Input], list[Output]], Generic[Input, Output]):
    __slots__ = 'node', '__len'
    __len: int
    node: BaseNode[Input, Output]

    def __init__(self, node: BaseNode[Input, Output], /) -> None:
        super().__init__()
        self.node = node
        self.__len = len(node)

    def __len__(self) -> int:
        return self.__len

    def copy(self) -> Self:
        return self.__class__(self.node.copy())

    def to_async(self) -> 'AsyncLoop[Input, Output]':
        return AsyncLoop(self.node.to_async())

    def process(self, args: Iterable[Input], reporter: Reporter) -> list[Output]:
        node = self.node
        results = (node.process(arg, reporter(f'i[{i}]')) for i, arg in enumerate(args))
        return [res for res in results if res is not None]


class AsyncLoop(Loop[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    async def process(self, args: Iterable[Input], reporter: Reporter) -> list[Output]:
        node = self.node
        tasks = (asyncio.create_task(node.process(arg, reporter(f'i[{i}]'))) for i, arg in enumerate(args))
        results = await asyncio.gather(*tasks)
        return [res for res in results if res is not None]


class Group(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = 'nodes', '__len'
    __len: int
    nodes: list[tuple[Any, BaseNode]]

    def __init__(self, nodes: list[tuple[Any, BaseNode]]):
        super().__init__()
        self.nodes = nodes
        self.__len = sum((len(node) for _, node in self.nodes))

    def __len__(self) -> int:
        return self.__len

    @staticmethod
    @abstractmethod
    def convert(results: Iterable[tuple[Any, Any]]) -> Output:
        """Converts the branched results to a specific collection type"""

    def copy(self) -> Self:
        return self.__class__([(branch, node.copy()) for branch, node in self.nodes])

    def to_async(self) -> 'AsyncGroup[Input, Output]':
        return AsyncGroup([(branch, node.to_async()) for branch, node in self.nodes])

    def process(self, arg: Input, reporter: Reporter) -> Output:
        return self.convert(
            (branch, result)
            for branch, result, severity
            in (
                (branch, node.process(arg, reporter(f'b[{branch}]')), node.severity)
                for branch, node in self.nodes
            )
            if not (result is None and severity is OPTIONAL)
        )


class AsyncGroup(Group[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output], metaclass=ABCMeta):
    async def process(self, arg: Input, reporter: Reporter) -> Output:
        branches, severities, tasks = zip(*[
            (branch,
             node.severity,
             asyncio.create_task(node.process(arg, reporter(f'b[{branch}]'))))
            for branch, node in self.nodes
        ])
        return self.convert(
            (branch, result)
            for branch, result, severity
            in zip(branches, await asyncio.gather(*tasks), severities, strict=True)
            if not (result is None and severity is OPTIONAL)
        )


def dict_converter(results: Iterable[tuple[Any, Any]]) -> dict:
    return {branch: result for branch, result in results}


def list_converter(results: Iterable[tuple[Any, Any]]) -> list:
    return [result for _, result in results]


class ListGroup(Group[Input, list], Generic[Input]):
    convert = staticmethod(list_converter)


class AsyncListGroup(AsyncGroup[Input, list], Generic[Input]):
    convert = staticmethod(list_converter)


class DictGroup(Group[Input, dict], Generic[Input]):
    convert = staticmethod(dict_converter)


class AsyncDictGroup(AsyncGroup[Input, dict], Generic[Input]):
    convert = staticmethod(dict_converter)


def is_node_async(obj) -> bool:
    """Checks whether the function or the collection contains an async function"""
    if isinstance(obj, AsyncBaseNode):
        return True
    elif callable(obj):
        return is_async(obj)
    elif isinstance(obj, (list, dict)):
        return any(map(is_node_async, obj.items() if isinstance(obj, dict) else obj))
    return False


def build(obj: Chainable[Input, Output]) -> BaseNode[Input, Output]:
    if isinstance(obj, BaseNode):
        return obj
    elif callable(obj):
        return Node(obj)
    elif isinstance(obj, (list, dict)):
        if isinstance(obj, dict):
            return DictGroup([(key, build(item)) for key, item in obj.items()])
        return ListGroup([(index, build(item)) for index, item in enumerate(obj)])
    elif obj is Ellipsis:
        return Chain()
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")


def async_build(obj) -> AsyncBaseNode:
    if isinstance(obj, BaseNode):
        return obj.to_async()
    elif callable(obj):
        return AsyncNode(asyncify(obj))
    elif isinstance(obj, (list, dict)):
        if isinstance(obj, dict):
            return AsyncDictGroup([(key, async_build(item)) for key, item in obj.items()])
        return AsyncListGroup([(index, async_build(item)) for index, item in enumerate(obj)])
    elif obj is Ellipsis:
        return AsyncChain()
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")
