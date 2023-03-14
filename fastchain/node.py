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
    TypeVar,
    Generic,
)

from ._util import asyncify
from .reporter import Reporter, Severity, OPTIONAL


Input = TypeVar('Input')
Output = TypeVar('Output')


class BaseNode(ABC, Generic[Input, Output]):
    """Base class for all fastchain nodes"""
    __slots__ = 'severity',
    severity: Severity

    def __init__(self):
        self.severity = Severity.NORMAL

    def __or__(self, other) -> 'Chain':
        pass

    def __mul__(self, other) -> 'Chain':
        pass

    def __call__(self, arg, /, reporter: Reporter | None = None) -> Output | None:
        """Processes arg and returns the result"""

    def __prepare_reporter__(self, reporter: Reporter) -> Reporter:
        pass

    @abstractmethod
    def _process(self, arg, reporter: Reporter) -> Output | None: ...

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode':
        """Returns an async copy of the current node"""


class AsyncBaseNode(BaseNode):
    def to_async(self) -> Self:
        return self.copy()

    @abstractmethod
    def _process(self, arg, reporter: Reporter) -> Output | None: ...

    async def __call__(self, arg, /, reporter: Reporter | None = None) -> Output | None:
        """Processes arg asynchronously and returns the result"""


class Node(BaseNode):
    __slots__ = 'name', 'func'
    name: str
    func: Callable[[Input], Output]

    def __init__(self, func: Callable[[Input], Output], name: str) -> None:
        super().__init__()
        self.func = func
        self.name = name

    def copy(self) -> Self:
        return self.__class__(self.func, self.name)

    def to_async(self, path: str | None = None) -> 'AsyncNode':
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
    __slots__ = 'nodes',
    nodes: list[BaseNode]

    def __init__(self, *nodes: BaseNode) -> None:
        super().__init__()
        self.nodes = list(nodes)

    def copy(self, path: str | None = None) -> Self:
        return self.__class__(*(node.copy() for node in self.nodes))

    def to_async(self, path: str | None = None) -> 'AsyncChain':
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


class AsyncChain(Chain, AsyncBaseNode):
    async def _process(self, arg, reporter: Reporter) -> Any:
        for node in self.nodes:
            res = await node(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class Loop(BaseNode):
    __slots__ = 'node',
    node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__()
        self.node = node

    def copy(self, path: str | None = None) -> Self:
        return self.__class__(self.node.copy())

    def to_async(self, path: str | None = None) -> 'AsyncLoop':
        return AsyncLoop(self.node.to_async())

    def _process(self, args: Iterable[Input], reporter: Reporter) -> list:
        node = self.node
        return [res for res in (node(arg, reporter) for arg in args) if res is not None]


class AsyncLoop(Loop, AsyncBaseNode):
    async def _process(self, args: Iterable, reporter: Reporter) -> list:
        node = self.node
        results = await asyncio.gather(*(asyncio.create_task(node(arg, reporter)) for arg in args))
        return [res for res in results if res is not None]


class Model(BaseNode):
    __slots__ = 'nodes',
    nodes: list[tuple[Any, BaseNode]]

    def __init__(self, nodes: list[tuple[Any, BaseNode]]):
        super().__init__()
        self.nodes = nodes

    @staticmethod
    @abstractmethod
    def convert(results: Iterable[tuple[Any, Any]]) -> Output:
        """Converts the branched results to a specific collection type"""

    def copy(self, path: str | None = None) -> Self:
        return self.__class__([(branch, node.copy()) for branch, node in self.nodes])

    def to_async(self, path: str | None = None) -> 'AsyncModel':
        return AsyncModel([(branch, node.to_async()) for branch, node in self.nodes])

    def _process(self, arg: Input, reporter: Reporter) -> Output:
        return self.convert(
            (branch, result)
            for branch, result, severity
            in ((branch, node(arg, reporter), node.severity) for branch, node in self.nodes)
            if not (result is None and severity is OPTIONAL)
        )


class AsyncModel(Model, AsyncBaseNode, metaclass=ABCMeta):
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


class ListModel(Model):
    convert = staticmethod(list_converter)


class AsyncListModel(AsyncModel):
    convert = staticmethod(list_converter)


class DictModel(Model):
    convert = staticmethod(dict_converter)


class AsyncDictModel(AsyncModel):
    convert = staticmethod(dict_converter)


def build(obj, name: str | None = None) -> BaseNode:
    pass


def async_build(obj, name: str | None = None) -> AsyncBaseNode:
    pass
