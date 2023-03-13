from __future__ import annotations
from abc import ABC, abstractmethod, ABCMeta
import asyncio
from typing import (
    Any,
    Self,
    Callable,
    Iterable,
    Coroutine,
    TypeVar,
)

from ._util import asyncify
from .reporter import Reporter, Severity, OPTIONAL, INHERIT


class BaseNode(ABC):
    """Base class for all fastchain nodes"""
    severity: Severity

    def __init__(self):
        self.severity = INHERIT

    @abstractmethod
    def copy(self) -> Self:
        """Returns an identical copy of the current node"""

    @abstractmethod
    def to_async(self) -> BaseNode:
        """Returns an async copy of the current node"""

    @abstractmethod
    def __call__(self, arg, reporter: Reporter) -> Any:
        """Implements the processing logic for the node"""


Input = TypeVar('Input')
Output = TypeVar('Output')


class Node(BaseNode):
    name: str
    func: Callable[[Input], Output]

    def __init__(self, func: Callable[[Input], Output], name: str) -> None:
        super().__init__()
        self.func = func
        self.name = name

    def copy(self) -> Self:
        return self.__class__(self.func, self.name)

    def to_async(self) -> AsyncNode:
        return AsyncNode(asyncify(self.func), self.name)

    def __call__(self, arg: Input, reporter: Reporter) -> Output | None:
        with reporter(self.name, self.severity, data=arg):
            return self.func(arg)


class AsyncNode(Node):
    func: Callable[[Input], Coroutine[None, None, Output]]

    async def __call__(self, arg: Input, reporter: Reporter) -> Output | None:
        with reporter(self.name, self.severity, data=arg):
            return await self.func(arg)


class Chain(BaseNode):
    nodes: list[BaseNode]

    def __init__(self, nodes: list[BaseNode]) -> None:
        super().__init__()
        self.nodes = nodes

    def copy(self) -> Self:
        return self.__class__([node.copy() for node in self.nodes])

    def to_async(self) -> AsyncChain:
        return AsyncChain([node.to_async() for node in self.nodes])

    def __call__(self, arg, reporter: Reporter) -> Any | None:
        for node in self.nodes:
            res = node(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(Chain):
    async def __call__(self, arg, reporter: Reporter) -> Any:
        for node in self.nodes:
            res = await node(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class Loop(BaseNode):
    node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__()
        self.node = node

    def copy(self) -> Self:
        return self.__class__(self.node.copy())

    def to_async(self) -> AsyncLoop:
        return AsyncLoop(self.node.to_async())

    def __call__(self, args: Iterable[Input], reporter: Reporter) -> list:
        node = self.node
        return [res for res in (node(arg, reporter) for arg in args) if res is not None]


class AsyncLoop(Loop):
    async def __call__(self, args: Iterable, reporter: Reporter) -> list:
        node = self.node
        results = await asyncio.gather(*(asyncio.create_task(node(arg, reporter)) for arg in args))
        return [res for res in results if res is not None]


class Model(BaseNode):
    nodes: list[tuple[Any, BaseNode]]

    def __init__(self, nodes: list[tuple[Any, BaseNode]]):
        super().__init__()
        self.nodes = nodes

    @staticmethod
    @abstractmethod
    def convert(results: Iterable[Any, Any]) -> Output:
        """Converts the branched results to a specific collection type"""

    def copy(self) -> Self:
        return self.__class__([(branch, node.copy()) for branch, node in self.nodes])

    def to_async(self) -> AsyncModel:
        return AsyncModel([(branch, node.to_async()) for branch, node in self.nodes])

    def __call__(self, arg: Input, reporter: Reporter) -> Output:
        return self.convert(
            (branch, result)
            for branch, result, severity
            in ((branch, node(arg, reporter), node.severity) for branch, node in self.nodes)
            if not (result is None and severity is OPTIONAL)
        )


class AsyncModel(Model, metaclass=ABCMeta):
    async def __call__(self, arg: Input, reporter: Reporter) -> Output:
        branches, severities, tasks = zip(*[
            (branch,
             node.severity,
             asyncio.create_task(node(arg, reporter(branch))))
            for branch, node in self.nodes
        ])
        return self.convert(
            (branch, result)
            for branch, result, severity
            in zip(branches, await asyncio.gather(*tasks), severities, strict=True)
            if not (result is None and severity is OPTIONAL)
        )


def dict_converter(results: Iterable[Any, Any]) -> dict:
    return {branch: result for branch, result in results}


def list_converter(results: Iterable[Any, Any]) -> list:
    return [result for _, result in results]


class ListModel(Model):
    convert = staticmethod(list_converter)


class AsyncListModel(AsyncModel):
    convert = staticmethod(list_converter)


class DictModel(Model):
    convert = staticmethod(dict_converter)


class AsyncDictModel(AsyncModel):
    convert = staticmethod(dict_converter)
