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
    Optional,
    Union,
    overload,
)

from ._util import asyncify, is_async, get_name, validate_name, get_varname
from .reporter import Reporter, Severity, OPTIONAL


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
    __slots__ = 'severity', 'root', 'name'
    name: str | None
    severity: Severity
    root: Optional['BaseNode']

    def __init__(self, root: Optional['BaseNode'] = None) -> None:
        self.name = None
        self.root = root
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

    def __call__(self, arg, /, reporter: Reporter | None = None) -> Output | None:
        """Processes arg and returns the result"""
        return self._process(arg, self.__prepare_reporter__(reporter))

    def __prepare_reporter__(self, reporter: Reporter) -> Reporter:
        pass

    def __set_severity(self, severity: Severity) -> None:
        if self.severity is not Severity.NORMAL:
            raise ValueError(f"node severity has already been set to {self.severity.name!r}")
        self.severity = severity

    def optional(self) -> Self:
        self.__set_severity(Severity.OPTIONAL)
        return self

    def required(self) -> Self:
        self.__set_severity(Severity.REQUIRED)
        return self

    def named(self, name: str) -> Self:
        self.name = validate_name(name)
        return self

    @abstractmethod
    def _process(self, arg, reporter: Reporter) -> Output | None: ...

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        """Returns an async copy of the current node"""


class AsyncBaseNode(BaseNode[Input, Coroutine[None, None, Output]], Generic[Input, Output]):
    def to_async(self) -> Self:
        return self.copy()

    @abstractmethod
    def _process(self, arg, reporter: Reporter) -> Output | None: ...


class Node(BaseNode):
    __slots__ = 'name', 'func'
    name: str
    func: Callable[[Input], Output]

    def __init__(self, func: Callable[[Input], Output], name: str) -> None:
        super().__init__()
        self.func = func
        self.name = name

    def __len__(self) -> int:
        return 1

    def copy(self) -> Self:
        return self.__class__(self.func, self.name)

    def to_async(self) -> 'AsyncNode[Input, Output]':
        return AsyncNode(asyncify(self.func), self.name)

    def _process(self, arg: Input, reporter: Reporter) -> Output | None:
        try:
            result = self.func(arg)
        except Exception as error:
            reporter.failure(self, error, self.severity, input=arg)
        else:
            reporter.success(self, input=arg, output=result)
            return result


class AsyncNode(Node, AsyncBaseNode):
    func: Callable[[Input], Coroutine[None, None, Output]]

    async def _process(self, arg: Input, reporter: Reporter) -> Output | None:
        try:
            result = await self.func(arg)
        except Exception as error:
            reporter.failure(self, error, self.severity, input=arg)
        else:
            reporter.success(self, input=arg, output=result)
            return result


class Chain(BaseNode):
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
        next_node = build(other)
        next_node.root = self
        self.nodes.append(next_node)
        self.__len += len(next_node)
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
        for node in self.nodes:
            res = node(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(Chain[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    def __or__(self, other):
        next_node = async_build(other)
        next_node.root = self
        self.nodes.append(next_node)
        self.__len += len(next_node)
        return self

    def __mul__(self, other):
        return self | AsyncLoop(async_build(other))

    async def _process(self, arg, reporter: Reporter) -> Any:
        for node in self.nodes:
            res = await node(arg, reporter)
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
        return [res for res in (node(arg, reporter) for arg in args) if res is not None]


class AsyncLoop(Loop[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    async def _process(self, args: Iterable[Input], reporter: Reporter) -> list[Output]:
        node = self.node
        results = await asyncio.gather(*(asyncio.create_task(node(arg, reporter)) for arg in args))
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
            in ((branch, node(arg, reporter), node.severity) for branch, node in self.nodes)
            if not (result is None and severity is OPTIONAL)
        )


class AsyncModel(Model[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output], metaclass=ABCMeta):
    async def _process(self, arg: Input, reporter: Reporter) -> Output:
        branches, severities, tasks = zip(*[
            (branch,
             node.severity,
             asyncio.create_task(node(arg, reporter)))
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
def nd(model: AsyncDictModelChainable[Input, Output]) -> AsyncDictModel[Input, Output]: ...
@overload
def nd(model: AsyncListModelChainable[Input, Output]) -> AsyncListModel[Input, Output]: ...
@overload
def nd(model: DictModelChainable[Input, Output]) -> DictModel[Input, Output]: ...
@overload
def nd(model: AsyncListModelChainable[Input, Output]) -> ListModel[Input, Output]: ...


def nd(obj=None) -> BaseNode:
    name = get_varname()
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
        if isinstance(obj, dict):
            return DictModel([(key, build(item)) for key, item in obj.items()])
        return ListModel([(index, build(item)) for index, item in enumerate(obj)])
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
