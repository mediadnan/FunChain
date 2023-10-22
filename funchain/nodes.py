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
from failures import Reporter, FailureException

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
Feedback: TypeAlias = tuple[bool, Output | None]


class OnFail(Enum):
    SKIP = 0    # Skips the node if it fails, as if it doesn't exist
    IGNORE = 1  # Ignores (never reports) the failure, but stops the chain
    REPORT = 2  # Reports the failures without raising any exception
    STOP = 3    # Raises the exception wrapped inside a special metadata class


class Failed(Exception):
    """This error get raised by a required node that failed; to stop the cascading execution"""


class BaseNode(ABC, Generic[Input, Output]):
    """Base class for all FunChain nodes"""
    __slots__ = ()

    def __or__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain([self]) | other

    def __mul__(self, other: Chainable[Output, Output2] | AsyncChainable[Output, Output2]) -> 'Chain[Output, Output2]':
        return Chain([self]) * other

    def __call__(self, arg, /, *, reporter: Reporter = None) -> Output | None:
        """Processes arg and returns the result"""
        try:
            _, res = self.process(arg, self._process_reporter(reporter))
            return res
        except Failed:
            return

    @staticmethod
    def _process_reporter(reporter: Reporter = None) -> Union[Reporter, type[Reporter]]:
        """Prepares the reporter"""
        if reporter is None:
            reporter = Reporter
        elif not isinstance(reporter, Reporter):
            raise TypeError("reporter must be instance of failures.Reporter")
        return reporter

    @abstractmethod
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]: ...

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        """Returns an async version of the current node"""

    def optional(self) -> Self:
        """Returns a node that get skipped in case of failure"""
        return OptionalNode(self)

    def required(self) -> Self:
        """Returns a mandatory node that stops the entire chain in case of failures"""
        return RequiredNode(self)

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

    def optional(self) -> Self:
        return AsyncOptionalNode(self)

    def required(self) -> Self:
        return AsyncRequiredNode(self)

    def rn(self, name: str | None = None) -> Self:
        return AsyncSemanticNode(self.copy(), name) if name is not None else self.copy()

    @abstractmethod
    async def process(self, arg, reporter: Reporter) -> Feedback[Output]: ...

    async def __call__(self, arg, /, *, reporter: Reporter = None) -> Output | None:
        try:
            _, res = await self.process(arg, self._process_reporter(reporter))
            return res
        except Failed:
            return


class Node(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = ('__func', '__name')
    __func: Callable[[Input], Output]
    __name: str

    def __init__(self, func: Callable[[Input], Output], name: str = None) -> None:
        super().__init__()
        self.__func = func
        if name is None:
            name = get_func_name(func)
        elif name == '<lambda>':
            name = 'lambda'
        else:
            validate_name(name)
        self.__name = name

    @property
    def func(self) -> Callable[[Input], Output]:
        """Gets the internal function"""
        return self.__func

    @property
    def name(self) -> str:
        """Gets the name of the leaf node (function)"""
        return self.__name

    def copy(self) -> Self:
        return self.__class__(self.__func, self.__name)

    def to_async(self) -> 'AsyncNode[Input, Output]':
        return AsyncNode(asyncify(self.__func), self.__name)

    def partial(self, *args, **kwargs) -> Self:
        """Clones the node and partially applies the arguments"""
        func = self.__func
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
        if name is None:
            return self.__class__(self.__func, get_func_name(self.__func))
        return self.__class__(self.__func, name)

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        try:
            return True, self.__func(arg)
        except Exception as error:
            reporter(self.name).report(error, input=arg)
            return False, None


class AsyncNode(Node[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    __func: Callable[[Input], Coroutine[None, None, Output]]

    async def process(self, arg: Input, reporter: Reporter) -> tuple[bool, Output]:
        try:
            return True, await self.func(arg)
        except Exception as error:
            reporter(self.name).report(error, input=arg)
            return False, None


class WrapperNode(BaseNode[Input, Output], Generic[Input, Output], ABC):
    __slots__ = ('__node',)
    __node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__()
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


class SemanticNode(WrapperNode[Input, Output], Generic[Input, Output]):
    """This node holds the label for to be reported in case of failure"""
    __slots__ = '__name',
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
            return self.copy()
        return self.__class__(self.node, name)

    def copy(self) -> Self:
        return self.__class__(self.node.copy(), self.name)

    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        return AsyncSemanticNode(self.node.to_async(), self.name)


class AsyncSemanticNode(SemanticNode[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    __node: AsyncBaseNode

    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        return await self.__node.process(arg, reporter(self.name))


class OptionalNode(WrapperNode[Input, Output | None], Generic[Input, Output]):
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        success, res = self.__node.process(arg, reporter)
        if success:
            return True, res
        return True, arg

    def to_async(self) -> 'AsyncOptionalNode[Input, Output]':
        return AsyncOptionalNode(self.__node.to_async())

    def optional(self) -> Self:
        """Returns the same optional node"""
        return self

    def required(self) -> Self:
        return RequiredNode(self.node)


class AsyncOptionalNode(OptionalNode[Input, Output], AsyncBaseNode[Input, Output | None], Generic[Input, Output]):
    node: AsyncBaseNode

    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        success, res = await self.node.process(arg, reporter)
        if success:
            return True, res
        return True, arg

    def required(self) -> Self:
        return AsyncRequiredNode(self.node)


class RequiredNode(WrapperNode[Input, Output], Generic[Input, Output]):
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        success, res = self.node.process(arg, reporter)
        if success:
            return True, res
        raise Failed

    def to_async(self) -> 'AsyncBaseNode[Input, Output]':
        return AsyncRequiredNode(self.node.to_async())

    def required(self) -> Self:
        """Returns the same required node"""
        return self

    def optional(self) -> Self:
        """Returns the optional node"""""
        return OptionalNode(self.node)


class AsyncRequiredNode(RequiredNode[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    node: AsyncBaseNode

    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        success, res = await self.node.process(arg, reporter)
        if success:
            return True, res
        raise Failed

    def optional(self) -> Self:
        return AsyncOptionalNode(self.node)


class Chain(BaseNode[Input, Output], Generic[Input, Output]):
    __slots__ = '__nodes',
    __nodes: list[BaseNode]

    def __init__(self, nodes: Iterable[BaseNode], /) -> None:
        super().__init__()
        self.__nodes = list(nodes)

    def __or__(self, other):
        if is_node_async(other):
            return self.to_async() | other
        return Chain([*self.__nodes, build(other)])

    def __mul__(self, other):
        if is_node_async(other):
            return self.to_async() * other
        return Chain([*self.__nodes, Loop(build(other))])

    @property
    def nodes(self) -> list[BaseNode]:
        """Gets a copy of the nodes (Read-only)"""
        return self.__nodes.copy()

    def copy(self) -> Self:
        return self.__class__([node.copy() for node in self.nodes])

    def to_async(self) -> 'AsyncChain[Input, Output]':
        return AsyncChain([node.to_async() for node in self.nodes])

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        for node in self.nodes:
            success, res = node.process(arg, reporter)
            if not success:
                return False, None
            arg = res
        return True, arg


class AsyncChain(Chain[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output]):
    __nodes: list[AsyncBaseNode]

    def __or__(self, other):
        return AsyncChain([*self.__nodes, async_build(other)])

    def __mul__(self, other):
        return AsyncChain([*self.__nodes, AsyncLoop(async_build(other))])

    async def process(self, arg, reporter: Reporter) -> Feedback[Output]:
        for node in self.__nodes:
            success, res = await node.process(arg, reporter)
            if not success:
                return False, None
            arg = res
        return True, arg


class Loop(WrapperNode[Iterable[Input], list[Output]], Generic[Input, Output]):
    def to_async(self) -> 'AsyncLoop[Input, Output]':
        return AsyncLoop(self.node.to_async())

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[[Output]]:
        node = self.node
        successes: set[bool] = set()
        results:  list[Output] = []
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
        self.__nodes = [(name, node.rn(name)) for name, node in nodes]

    @staticmethod
    @abstractmethod
    def convert(results: Iterable[tuple[Any, Any]]) -> Output:
        """Converts the branched results to a specific collection type"""

    def copy(self) -> Self:
        return self.__class__([(branch, node.copy()) for branch, node in self.__nodes])

    def to_async(self) -> 'AsyncGroup[Input, Output]':
        return AsyncGroup([(branch, node.to_async()) for branch, node in self.__nodes])

    @property
    def nodes(self) -> list[tuple[Any, BaseNode]]:
        return self.__nodes.copy()

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        ((name, *node.process(arg, reporter)) for name, node in self.__nodes)


class AsyncGroup(Group[Input, Output], AsyncBaseNode[Input, Output], Generic[Input, Output], metaclass=ABCMeta):
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        branches, severities, tasks = zip(
            *[
                (branch,
                 node.severity,
                 asyncio.create_task(node.process(arg, reporter(f'b[{branch}]'))))
                for branch, node in self.__nodes
            ]
        )
        return self.convert(
            (branch, result)
            for branch, result, severity
            in zip(branches, await asyncio.gather(*tasks), severities, strict=True)
            if not (result is None and severity is OPTIONAL)
        )


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
