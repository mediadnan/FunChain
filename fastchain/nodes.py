"""
The module defines different types of fastchain nodes,
nodes are built and used by fastchain chains
to perform the data processing.
"""
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

from .reporter import Reporter, Severity, OPTIONAL, FailureData, FailureLogger
from ._util import asyncify, is_async, get_name, validate_name
from .util.names import get_func_name, guess_var_name

Input = TypeVar('Input')
Output = TypeVar('Output')
Output2 = TypeVar('Output2')

AsyncCallable: TypeAlias = Callable[[Input], Coroutine[None, None, Output]]
Chainable: TypeAlias = Union[
    'BaseNode[Input, Output]',
    Callable[[Input], Output],
    'DictModelChainable[Input]',
    'ListModelChainable[Input]'
]
AsyncChainable: TypeAlias = Union[
    'AsyncBaseNode[Input, Output]',
    AsyncCallable[Input, Output],
    'AsyncDictModelChainable[Input]',
    'AsyncListModelChainable[Input]'
]
DictModelChainable: TypeAlias = dict[Any, Chainable[Input, Any]]
ListModelChainable: TypeAlias = list[Chainable[Input, Any]]
AsyncDictModelChainable: TypeAlias = dict[Any, AsyncChainable[Input, Any] | Chainable[Input, Any]]
AsyncListModelChainable: TypeAlias = list[AsyncChainable[Input, Any] | Chainable[Input, Any]]


class BaseNode(ABC, Generic[Input, Output]):
    """Base class for all fastchain nodes"""
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
    def __or__(self, other: AsyncDictModelChainable[Output]) -> 'AsyncChain[Input, dict]': ...
    @overload
    def __or__(self, other: DictModelChainable[Output]) -> 'Chain[Input, dict]': ...
    @overload
    def __or__(self, other: AsyncListModelChainable[Output]) -> 'AsyncChain[Input, list]': ...
    @overload
    def __or__(self, other: ListModelChainable[Output]) -> 'Chain[Input, list]': ...

    def __or__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain(self) | other

    @overload
    def __mul__(self, other: 'AsyncBaseNode[Output, Output2]') -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: 'BaseNode[Output, Output2]') -> 'Chain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: AsyncCallable[Output, Output2]) -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: Callable[[Output], Output2]) -> 'Chain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: AsyncDictModelChainable[Output]) -> 'AsyncChain[Input, list[dict]]': ...
    @overload
    def __mul__(self, other: DictModelChainable[Output]) -> 'Chain[Input, list[dict]]': ...
    @overload
    def __mul__(self, other: AsyncListModelChainable[Output]) -> 'AsyncChain[Input, list[list]]': ...
    @overload
    def __mul__(self, other: ListModelChainable[Output]) -> 'Chain[Input, list[list]]': ...

    def __mul__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain(self) * other

    @abstractmethod
    def __len__(self) -> int: ...

    def __repr__(self) -> str:
        name = guess_var_name()
        name = f'{name!r}, ' if name else ''
        return f'fastchain.{self.__class__.__name__}({name}nodes={self.__len__()})'

    def __call__(
            self,
            arg, /, *,
            name: str | None = None,
            handler: Callable[[FailureData], None] = FailureLogger()
    ) -> Output | None:
        """Processes arg and returns the result"""
        if name is None:
            name = guess_var_name()
        return self._process(arg, Reporter(name, handler))

    def optional(self) -> Self:
        new = self.copy()
        new.severity = Severity.OPTIONAL
        return new

    def required(self) -> Self:
        new = self.copy()
        new.severity = Severity.REQUIRED
        return new

    def named(self, name: str) -> Self:
        new = self.copy()
        new.name = validate_name(name)
        return new

    @abstractmethod
    def _process(self, arg, reporter: Reporter) -> Output | None: ...

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
    def __or__(self, other: DictModelChainable[Output]) -> 'AsyncChain[Input, dict]': ...
    @overload
    def __or__(self, other: ListModelChainable[Output]) -> 'AsyncChain[Input, list]': ...

    def __or__(self, other):
        return AsyncChain(self) | other

    @overload
    def __mul__(self, other: 'BaseNode[Output, Output2]') -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: Callable[[Output], Output2]) -> 'AsyncChain[Input, list[Output2]]': ...
    @overload
    def __mul__(self, other: DictModelChainable[Output]) -> 'AsyncChain[Input, list[dict]]': ...
    @overload
    def __mul__(self, other: ListModelChainable[Output]) -> 'AsyncChain[Input, list[list]]': ...

    def __mul__(self, other):
        return AsyncChain(self) * other

    def to_async(self) -> Self:
        """Returns the current node"""
        return self

    @abstractmethod
    def _process(self, arg, reporter: Reporter) -> Output | None: ...


class Node(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = 'func', 'name'
    name: str
    func: Callable[[Input], Output]

    def __init__(self, func: Callable[[Input], Output], name: str | None = None) -> None:
        super().__init__()
        self.func = func
        self.name = name if (name is not None and validate_name(name)) else get_func_name(func)

    def __len__(self) -> int:
        return 1

    def copy(self) -> Self:
        return self.__class__(self.func, self.name)

    def to_async(self) -> 'AsyncNode[Input, Output]':
        return AsyncNode(asyncify(self.func), self.name)

    def named(self, name: str) -> Self:
        new = self.copy()
        new.name = validate_name(name)
        return new

    def _process(self, arg: Input, reporter: Reporter) -> Output | None:
        with reporter(self.name, severity=self.severity, input=arg):
            return self.func(arg)


class AsyncNode(Node[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    func: Callable[[Input], Coroutine[None, None, Output]]

    async def _process(self, arg: Input, reporter: Reporter) -> Output | None:
        with reporter(self.name, severity=self.severity, input=arg):
            return await self.func(arg)


class Chain(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = 'nodes', '__len'
    __len: int
    nodes: list[BaseNode]

    def __init__(self, *nodes: BaseNode) -> None:
        super().__init__()
        self.nodes = list(nodes)
        self.__len = sum(map(len, nodes))

    def __or__(self, other):
        if is_node_async(other):
            return self.to_async() | other
        nxt = build(other)
        self.__len += len(nxt)
        self.nodes.append(nxt)
        return self

    def __mul__(self, other):
        if is_node_async(other):
            return self.to_async() * other
        return self | Loop(build(other))

    def __len__(self) -> int:
        return self.__len

    def copy(self) -> Self:
        return self.__class__(*(node.copy() for node in self.nodes))

    def to_async(self) -> 'AsyncChain[Input, Output]':
        return AsyncChain(*(node.to_async() for node in self.nodes))

    def _process(self, arg, reporter: Reporter) -> Any | None:
        for index, node in enumerate(self.nodes):
            res = node._process(arg, reporter(f'c[{index}]'))
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(Chain[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    def __or__(self, other):
        return AsyncChain(*self.nodes, async_build(other))

    def __mul__(self, other):
        return AsyncChain(*self.nodes, AsyncLoop(async_build(other)))

    async def _process(self, arg, reporter: Reporter) -> Any:
        for index, node in enumerate(self.nodes):
            res = await node._process(arg, reporter(f'c[{index}]'))
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

    def _process(self, args: Iterable[Input], reporter: Reporter) -> list[Output]:
        node = self.node
        results = (node._process(arg, reporter(f'i[{i}]')) for i, arg in enumerate(args))
        return [res for res in results if res is not None]


class AsyncLoop(Loop[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    async def _process(self, args: Iterable[Input], reporter: Reporter) -> list[Output]:
        node = self.node
        tasks = (asyncio.create_task(node._process(arg, reporter(f'i[{i}]'))) for i, arg in enumerate(args))
        results = await asyncio.gather(*tasks)
        return [res for res in results if res is not None]


class Model(BaseNode[Input, Output], Generic[Input, Output]):
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

    def to_async(self) -> 'AsyncModel[Input, Output]':
        return AsyncModel([(branch, node.to_async()) for branch, node in self.nodes])

    def _process(self, arg: Input, reporter: Reporter) -> Output:
        return self.convert(
            (branch, result)
            for branch, result, severity
            in (
                (branch, node._process(arg, reporter(f'b[{branch}]')), node.severity)
                for branch, node in self.nodes
            )
            if not (result is None and severity is OPTIONAL)
        )


class AsyncModel(Model[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output], metaclass=ABCMeta):
    async def _process(self, arg: Input, reporter: Reporter) -> Output:
        branches, severities, tasks = zip(*[
            (branch,
             node.severity,
             asyncio.create_task(node._process(arg, reporter(f'b[{branch}]'))))
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


class ListModel(Model[Input, list], Generic[Input]):
    convert = staticmethod(list_converter)


class AsyncListModel(AsyncModel[Input, list], Generic[Input]):
    convert = staticmethod(list_converter)


class DictModel(Model[Input, dict], Generic[Input]):
    convert = staticmethod(dict_converter)


class AsyncDictModel(AsyncModel[Input, dict], Generic[Input]):
    convert = staticmethod(dict_converter)


@overload
def nd() -> Chain[Input, Input]: ...
@overload
def nd(fun: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def nd(fun: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def nd(fun: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def nd(fun: Callable[[Any], Any]) -> Node[Input, Output]: ...
@overload
def nd(model: AsyncDictModelChainable[Input]) -> AsyncDictModel[Input]: ...
@overload
def nd(model: AsyncListModelChainable[Input]) -> AsyncListModel[Input]: ...
@overload
def nd(model: DictModelChainable[Input]) -> DictModel[Input]: ...
@overload
def nd(model: AsyncListModelChainable[Input]) -> ListModel[Input]: ...


def nd(obj=None) -> BaseNode:
    if obj is None:
        return Chain()
    elif is_node_async(obj):
        return async_build(obj)
    return build(obj)


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
        if isinstance(obj, AsyncBaseNode):
            raise TypeError("Cannot build a normal node from and async node")
        return obj.copy()
    elif callable(obj):
        if is_async(obj):
            raise TypeError("Cannot build a normal node from and async function")
        return Node(obj, get_name(obj))
    elif isinstance(obj, (list, dict)):
        model, items = ((DictModel, obj.items()) if isinstance(obj, dict) else (ListModel, enumerate(obj)))
        nodes: list[Any, BaseNode] = []
        for branch, item in items:
            node = build(item).named(str(branch))
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")


def async_build(obj) -> AsyncBaseNode:
    if isinstance(obj, BaseNode):
        return obj.to_async()
    elif callable(obj):
        return AsyncNode(asyncify(obj), get_name(obj))
    elif isinstance(obj, (list, dict)):
        if isinstance(obj, dict):
            return AsyncDictModel([(key, async_build(item)) for key, item in obj.items()])
        return AsyncListModel([(index, async_build(item)) for index, item in enumerate(obj)])
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")
