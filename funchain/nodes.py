import asyncio
import functools
from abc import ABC, abstractmethod, ABCMeta
from enum import Enum
from typing import (TypeVar,
                    ParamSpec,
                    TypeAlias,
                    Union,
                    Callable,
                    Coroutine,
                    Any,
                    Generic,
                    Self,
                    Iterable, Literal, )
from failures import Reporter

from .name import get_func_name, validate as validate_name

Input = TypeVar('Input')
Output = TypeVar('Output')
Output2 = TypeVar('Output2')
SPEC = ParamSpec('SPEC')
RT = TypeVar('RT')

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
Feedback: TypeAlias = Union[tuple[Literal[True], Output], tuple[Literal[False], None]]


class Severity(Enum):
    OPTIONAL = 0  # Basically indicates that the failure should be ignored
    NORMAL = 1  # Indicates that the failure should be reported but without failure
    REQUIRED = 2  # Indicates that the failure should be handled and the process should stop


# severity shortcuts
OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED


class BaseNode(ABC, Generic[Input, Output]):
    """Base class for all FunChain nodes"""
    __slots__ = '_severity', '_name'
    _severity: Severity
    _name: str | None

    def __init__(self) -> None:
        self.severity = NORMAL

    def __or__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain(self) | other

    def __mul__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain(self) * other

    def __repr__(self) -> str:
        return f"FunChain.{self.__class__.__name__}({self.__len__()})"

    def __call__(self, arg, /, *, reporter: Reporter = None) -> Output | None:
        """Processes arg and returns the result"""
        if reporter is None:
            reporter = Reporter
        elif not isinstance(reporter, Reporter):
            raise TypeError("reporter must be instance of failures.Reporter")
        return self.process(arg, (reporter or Reporter))

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        ...

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        """Returns an async version of the current node"""

    @property
    def severity(self) -> Severity:
        """Gets the severity level of the node."""
        return self._severity

    @severity.setter
    def severity(self, severity: Severity) -> None:
        if not isinstance(severity, Severity):
            raise TypeError("Node severity must be either OPTIONAL, NORMAL or REQUIRED")
        self._severity = severity

    @property
    def name(self) -> str | None:
        """Gets the name of the node"""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        validate_name(name)
        self._name = name

    def rn(self, name: str | None = None) -> Self:
        """Clones the node with a new name"""
        _node = self.copy()
        _node.name = name
        return _node


class AsyncBaseNode(BaseNode[Input, Coroutine[None, None, Output]], Generic[Input, Output]):
    def __or__(self, other) -> AsyncChainable[Input, Output2]:
        return AsyncChain(self) | other

    def __mul__(self, other) -> AsyncChainable[Input, Output2]:
        return AsyncChain(self) * other

    def to_async(self) -> Self:
        """Returns a clone for the current node"""
        return self.copy()

    @abstractmethod
    async def process(self, arg, reporter: Reporter) -> Feedback[Output]: ...


class SemanticNode(BaseNode):
    """This node holds the label for to be reported in case of failure"""
    __slots__ = '__node',
    __label: str
    __node: BaseNode

    def __int__(self, label: str, node: BaseNode) -> None:
        validate_name(label)
        self.__label = label
        self.__node = node

    def __len__(self) -> int:
        return len(self.__node)

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        return self.__node.process(arg, reporter(self.__label))

    def copy(self) -> Self:
        # TODO: implement
        pass

    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        pass


class Node(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = 'func',
    func: Callable[[Input], Output]

    def __init__(self, func: Callable[[Input], Output], *, name: str = None, severity: Severity = NORMAL) -> None:
        if name is None:
            name = get_func_name(func)
        super().__init__(name=name, severity=severity)
        self.func = func

    def __len__(self) -> int:
        return 1

    def copy(self) -> Self:
        return self.__class__(self.func, name=self.name, severity=self.severity)

    def to_async(self) -> 'AsyncNode[Input, Output]':
        return AsyncNode(asyncify(self.func), name=self.name, severity=self.severity)

    def partial(self, *args, **kwargs) -> Self:
        """Clones the node and partially applies the arguments"""
        _node = self.copy()
        func = self.func
        while isinstance(func, functools.partial):
            args = *func.args, *args
            kwargs = {**func.keywords, **kwargs}
            func = func.func
        _node.func = functools.partial(func, *args, **kwargs)
        return _node

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        try:
            return True, self.func(arg)
        except Exception as error:
            reporter(self.name).report(error, input=arg)
            return False, None


class AsyncNode(Node[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    func: Callable[[Input], Coroutine[None, None, Output]]

    async def process(self, arg: Input, reporter: Reporter) -> tuple[bool, Output]:
        try:
            return True, await self.func(arg)
        except Exception as error:
            reporter(self.name).report(error, input=arg)
            return False, None


class Chain(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = '__nodes', '__len'
    __len: int
    __nodes: list[BaseNode]

    def __init__(self, *nodes: BaseNode) -> None:
        super().__init__()
        self.__nodes = list(nodes)
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

    @property
    def nodes(self) -> list[BaseNode]:
        """Gets the list of nodes (Read-only)"""
        return self.__nodes

    def copy(self) -> Self:
        return self.__class__(*(node.copy() for node in self.nodes))

    def to_async(self) -> 'AsyncChain[Input, Output]':
        return AsyncChain(*(node.to_async() for node in self.nodes))

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        if self.name is not None:
            reporter = reporter(self.name)
        for node in self.nodes:
            success, res = node.process(arg, reporter)
            if not success:
                if node.severity is OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


class AsyncChain(Chain[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    __nodes: list[AsyncBaseNode]

    def __or__(self, other):
        nxt = async_build(other)
        return AsyncChain(*self.__nodes, nxt) if nxt else self.copy()

    def __mul__(self, other):
        nxt = async_build(other)
        return AsyncChain(*self.__nodes, AsyncLoop(nxt)) if nxt else self.copy()

    async def process(self, arg, reporter: Reporter) -> Feedback[Output]:
        if self.name is not None:
            reporter = reporter(self.name)
        for node in self.__nodes:
            success, res = await node.process(arg, reporter)
            if not success:
                if node.severity is OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


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

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[Output]:
        node = self.node
        results = (node.process(arg, reporter(f'i[{i}]')) for i, arg in enumerate(args))
        return [res for res in results if res is not None]


class AsyncLoop(Loop[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    async def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[Output]:
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

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
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
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        branches, severities, tasks = zip(
            *[
                (branch,
                 node.severity,
                 asyncio.create_task(node.process(arg, reporter(f'b[{branch}]'))))
                for branch, node in self.nodes
            ]
        )
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


def is_async(func: Callable) -> bool:
    """
    Checks if the function / callable is defined as asynchronous

    :param func: the function to be checked
    :return: True if function is async else False
    """
    # Inspired from the Starlette library
    # https://github.com/encode/starlette/blob/4fdfad20abf8981e15babe015eb5d8330d9c7662/starlette/_utils.py#L13
    while isinstance(func, functools.partial):
        func = func.func
    return asyncio.iscoroutinefunction(func) or asyncio.iscoroutinefunction(getattr(func, '__call__', None))


def asyncify(func: Callable[SPEC, RT], /) -> Callable[SPEC, Coroutine[None, None, RT]]:
    """
    Wraps blocking function to be called in a separate loop's (default) executor

    :param func: the function to be asynchronified
    :return: async version of function
    """

    @functools.wraps(func)
    async def async_func(*args: SPEC.args, **kwargs: SPEC.kwargs) -> Coroutine[None, None, RT]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    return func if is_async(func) else async_func


def is_node_async(obj) -> bool:
    """Checks whether the function or the collection contains an async function"""
    return (
            isinstance(obj, AsyncBaseNode)
            or (callable(obj) and is_async(obj))
            or (isinstance(obj, (list, dict)) and any(map(is_node_async, obj.items() if isinstance(obj, dict) else obj)))
    )


def build(obj: Chainable[Input, Output]) -> BaseNode[Input, Output]:
    if isinstance(obj, BaseNode):
        return obj.copy()
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
