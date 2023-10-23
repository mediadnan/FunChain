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
                    Iterable)
from failures import Reporter

from .name import validate as validate_name

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
DictGroupChainable: TypeAlias = dict[str, Chainable[Input, Any]]
ListGroupChainable: TypeAlias = list[Chainable[Input, Any]]
AsyncDictGroupChainable: TypeAlias = dict[str, AsyncChainable[Input, Any] | Chainable[Input, Any]]
AsyncListGroupChainable: TypeAlias = list[AsyncChainable[Input, Any] | Chainable[Input, Any]]
Feedback: TypeAlias = tuple[bool, Output | None]


class Severity(Enum):
    OPTIONAL = -1
    NORMAL = 0
    REQUIRED = 1


OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED


class Failed(Exception):
    """This error gets raised by a required node that failed; to stop the cascading execution"""


class BaseNode(ABC, Generic[Input, Output]):
    """Base class for all FunChain nodes"""
    __slots__ = ('__severity',)
    __severity: Severity

    def __init__(self, severity: Severity = NORMAL) -> None:
        self.severity = severity

    def __or__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain([self]) | other

    def __mul__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain([self]) * other

    def __call__(self, arg, /, *, reporter: Reporter = None) -> Output | None:
        """Processes arg and returns the result"""
        try:
            return self.process(arg, self._process_reporter(reporter))[1]
        except Failed:
            return

    @staticmethod
    def _process_reporter(reporter: Reporter = None) -> Union[Reporter, type[Reporter]]:
        """Prepares the reporter"""
        if reporter is None:
            return Reporter
        elif isinstance(reporter, Reporter):
            return reporter
        raise TypeError("reporter must be instance of failures.Reporter")

    @abstractmethod
    def process(self, arg: Input, reporter: Union[Reporter, type[Reporter]]) -> Feedback[Output]: ...

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        """Returns an async version of the current node"""

    @property
    def severity(self) -> Severity:
        """Gets the node severity"""
        return self.__severity

    @severity.setter
    def severity(self, severity: Severity) -> None:
        if not isinstance(severity, Severity):
            raise TypeError("severity must be either NORMAL, OPTIONAL or REQUIRED")
        self.__severity = severity

    def optional(self) -> Self:
        """Returns a node that gets skipped in case of failure"""
        new = self.copy()
        new.severity = OPTIONAL
        return new

    def required(self) -> Self:
        """Returns a mandatory node that stops the entire chain in case of failures"""
        new = self.copy()
        new.severity = REQUIRED
        return new

    def rn(self, name: str | None = None) -> Self:
        """Clones the node with a new name"""
        return SemanticNode(self.copy(), name) if name is not None else self.copy()


class AsyncBaseNode(BaseNode[Input, Coroutine[None, None, Output]], Generic[Input, Output]):
    def __or__(self, other) -> AsyncChainable[Input, Output2]:
        return AsyncChain([self]) | other

    def __mul__(self, other) -> AsyncChainable[Input, Output2]:
        return AsyncChain([self]) * other

    def to_async(self) -> Self:
        """Returns a clone for the current node"""
        return self.copy()

    def rn(self, name: str | None = None) -> Self:
        return AsyncSemanticNode(self.copy(), name) if name is not None else self.copy()

    @abstractmethod
    async def process(self, arg, reporter: Reporter) -> Feedback[Output]: ...

    async def __call__(self, arg, /, *, reporter: Reporter = None) -> Output | None:
        try:
            return (await self.process(arg, self._process_reporter(reporter)))[1]
        except Failed:
            return


class Node(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = ('__fun', '__name')
    __fun: Callable[[Input], Output]
    __name: str

    def __init__(self, fun: Callable[[Input], Output], name: str = None, severity: Severity = NORMAL) -> None:
        super().__init__(severity=severity)
        self.__fun = fun
        self.name = name

    @property
    def fun(self) -> Callable[[Input], Output]:
        """Gets the internal function"""
        return self.__fun

    @property
    def name(self) -> str:
        """Gets the name of the leaf node (function)"""
        return self.__name

    @name.setter
    def name(self, name: str | None) -> None:
        if name is None:
            try:
                name = self.__fun.__name__
                if name == '<lambda>':
                    name = 'lambda'
            except AttributeError:
                name = type(self.__fun).__name__
        else:
            validate_name(name)
        self.__name = name

    def copy(self) -> Self:
        return self.__class__(self.__fun, self.__name)

    def to_async(self) -> 'AsyncNode[Input, Output]':
        return AsyncNode(asyncify(self.__fun), self.__name)

    def partial(self, *args, **kwargs) -> Self:
        """Clones the node and partially applies the arguments"""
        func = self.__fun
        while isinstance(func, functools.partial):
            args = *func.args, *args
            kwargs = {**func.keywords, **kwargs}
            func = func.func
        return self.__class__(functools.partial(func, *args, **kwargs), self.__name)

    def rn(self, name: str | None = None) -> Self:
        """
        Returns a clone of the current node with the new name,
        or a clone with the default function name if no name is passed
        """
        return self.__class__(self.__fun, name)

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        try:
            return True, self.__fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    def handle_failure(self, error: Exception, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Reports the failure according to the node severity"""
        severity = self.severity
        if severity is not OPTIONAL:
            reporter(self.name).report(error, input=arg)
        if severity is REQUIRED:
            raise Failed
        return False, None


class AsyncNode(Node[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    __fun: Callable[[Input], Coroutine[None, None, Output]]

    async def process(self, arg: Input, reporter: Reporter) -> tuple[bool, Output]:
        try:
            return True, await self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)


class WrapperNode(BaseNode[Input, Output], Generic[Input, Output], metaclass=ABCMeta):
    __slots__ = ('__node',)
    __node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__(severity=node.severity)
        self.__node = node

    @property
    def node(self) -> BaseNode:
        """Returns the wrapped node (Read-only)"""
        return self.__node

    @node.setter
    def node(self, node: BaseNode) -> None:
        if not isinstance(node, BaseNode):
            raise TypeError("node must be instance of failures.BaseNode")
        self.__node = node

    def copy(self) -> Self:
        return self.__class__(self.__node.copy())

    def optional(self) -> Self:
        return self.__class__(self.__node.optional())

    def required(self) -> Self:
        return self.__class__(self.__node.required())


class SemanticNode(WrapperNode[Input, Output], Generic[Input, Output]):
    """This node holds the label for to be reported in case of failure"""
    __slots__ = ('__name',)
    __name: str

    def __init__(self, node: BaseNode, /, label: str) -> None:
        super().__init__(node)
        validate_name(label)
        self.__name = label

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        return self.node.process(arg, reporter(self.name))

    @property
    def name(self) -> str:
        """Gets the label of the node (Read-only)"""
        return self.__name

    def rn(self, name: str | None = None) -> Self:
        if name is None:
            return self.node.copy()
        return self.__class__(self.node, name)

    def copy(self) -> Self:
        return self.__class__(self.node.copy(), self.name)

    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        return AsyncSemanticNode(self.node.to_async(), self.name)


class AsyncSemanticNode(SemanticNode[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    node: AsyncBaseNode

    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        return await self.node.process(arg, reporter(self.name))


class Chain(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = '__nodes',
    __nodes: list[BaseNode]

    def __init__(self, nodes: Iterable[BaseNode], /, severity: Severity = NORMAL) -> None:
        super().__init__(severity=severity)
        self.__nodes = list(nodes)

    def __or__(self, other):
        if is_node_async(other):
            return self.to_async() | other
        return Chain([*self.__nodes, build(other)], severity=self.severity)

    def __mul__(self, other):
        if is_node_async(other):
            return self.to_async() * other
        return Chain([*self.__nodes, Loop(build(other))], severity=self.severity)

    @property
    def nodes(self) -> list[BaseNode]:
        """Gets a copy of the nodes (Read-only)"""
        return self.__nodes.copy()

    def copy(self) -> Self:
        return self.__class__([node.copy() for node in self.nodes], severity=self.severity)

    def to_async(self) -> 'AsyncChain[Input, Output]':
        return AsyncChain([node.to_async() for node in self.nodes], severity=self.severity)

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        for node in self.nodes:
            success, res = node.process(arg, reporter)
            if not success:
                if node.severity is OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


class AsyncChain(Chain[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    nodes: list[AsyncBaseNode]

    def __or__(self, other):
        return AsyncChain([*self.nodes, async_build(other)], severity=self.severity)

    def __mul__(self, other):
        return AsyncChain([*self.nodes, AsyncLoop(async_build(other))], severity=self.severity)

    async def process(self, arg, reporter: Reporter) -> Feedback[Output]:
        for node in self.nodes:
            success, res = await node.process(arg, reporter)
            if not success:
                if node.severity is OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


class Loop(WrapperNode[Iterable[Input], list[Output]], Generic[Input, Output]):
    def to_async(self) -> 'AsyncLoop[Input, Output]':
        return AsyncLoop(self.node.to_async())

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[Output]:
        node = self.node
        successes: set[bool] = set()
        results: list[Output] = []
        for arg in args:
            success, res = node.process(arg, reporter)
            successes.add(success)
            results.append(res)
        return any(successes), results


class AsyncLoop(Loop[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    node: AsyncBaseNode

    async def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[Output]:
        node = self.node
        jobs = await asyncio.gather(*[asyncio.create_task(node.process(arg, reporter)) for arg in args])
        successes, results = zip(*jobs)
        return any(successes), results


class Group(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = ('__nodes',)
    __nodes: list[tuple[str, BaseNode]]

    def __init__(self, nodes: Iterable[tuple[str, BaseNode]], /):
        super().__init__()
        self.__nodes = list(nodes)

    @staticmethod
    @abstractmethod
    def convert(results: Iterable[tuple[Any, Any]]) -> Output:
        """Converts the branched results to a specific collection type"""

    def copy(self) -> Self:
        return self.__class__([(branch, node.copy()) for branch, node in self.__nodes])

    def to_async(self) -> 'AsyncGroup[Input, Output]':
        return AsyncGroup([(branch, node.to_async()) for branch, node in self.__nodes])

    @property
    def nodes(self) -> list[tuple[str, BaseNode]]:
        return self.__nodes.copy()

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        successes: set[bool] = set()
        results: list[tuple[str, Any]] = []
        for name, node in self.__nodes:
            success, result = node.process(arg, reporter)
            if not success:
                if node.severity is OPTIONAL:
                    continue
                if node.severity is REQUIRED:
                    raise Failed
            successes.add(success)
            results.append((name, result))
        return any(successes), self.convert(results)


class AsyncGroup(Group[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output], metaclass=ABCMeta):
    nodes: list[tuple[str, AsyncBaseNode]]

    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        names, severities, tasks = zip(
            *((name, node.severity, asyncio.create_task(node.process(arg, reporter))) for name, node in self.nodes)
        )
        successes, results = zip(*(await asyncio.gather(*tasks)))
        for name, success, severity, result in zip(names, successes, severities, results):
            if not success:
                if severity is OPTIONAL:
                    continue
                if severity is REQUIRED:
                    raise Failed
            successes.add(success)
            results.append((name, result))
        return any(successes), self.convert(results)


def dict_converter(results: Iterable[tuple[str, Any]]) -> dict:
    return {branch: result for branch, result in results}


def list_converter(results: Iterable[tuple[str, Any]]) -> list:
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
            return DictGroup([(key, SemanticNode(build(item), str(key))) for key, item in obj.items()])
        return ListGroup([(index, SemanticNode(build(item), str(index))) for index, item in enumerate(obj)])
    elif obj is Ellipsis:
        return Chain([])
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")


def async_build(obj) -> AsyncBaseNode:
    if isinstance(obj, BaseNode):
        return obj.to_async()
    elif callable(obj):
        return AsyncNode(asyncify(obj))
    elif isinstance(obj, (list, dict)):
        if isinstance(obj, dict):
            return AsyncDictGroup([(key, AsyncSemanticNode(async_build(item), str(key))) for key, item in obj.items()])
        return AsyncListGroup(
            [(index, AsyncSemanticNode(async_build(item), str(index))) for index, item in enumerate(obj)]
        )
    elif obj is Ellipsis:
        return AsyncChain([])
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")
