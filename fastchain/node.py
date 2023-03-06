import abc
import asyncio
from typing import (
    Any,
    Self,
    Generic,
    TypeVar,
    Callable,
    Iterable,
    Coroutine,
    TypeAlias,
)

from ._util import get_name, asyncify, get_varname, is_async
from .reporter import Reporter, Severity, OPTIONAL, INHERIT

T = TypeVar('T')
Input = TypeVar('Input')
Output = TypeVar('Output')
Output2 = TypeVar('Output2')

Chainable: TypeAlias = ('BaseNode[Input, Output]' |
                        Callable[[Input], Output] |
                        dict[Any, 'Chainable[Input, Output]'] |
                        list['Chainable[Input, Output]'])


AsyncChainable: TypeAlias = ('AsyncBaseNode[Input, Output]' |
                             Callable[[Input], Coroutine[None, None, Output]] |
                             dict[Any, 'AsyncChainable[Input, Output]'] |
                             list['AsyncChainable[Input, Output]'])


Feedback: TypeAlias = Output | None


class BaseNode(Generic[T, Input, Output]):
    """Base class for all fastchain nodes"""
    __core: T
    name: str
    severity: Severity
    parent: 'BaseNode' | None

    def __init__(self, core: T, /) -> None:
        self.__core = core
        self.severity = INHERIT
        self.__name: str | None = None
        self.__parent: BaseNode | None = None

    def __call__(self, arg: Input, /, reporter: Reporter | None = None) -> Output | None:
        reporter = self._rep_prep(reporter)
        return self.process(arg, reporter)

    def copy(self) -> Self:
        new = self.__class__(self.__core)
        new.__dict__.update(self.__dict__)
        return new

    @abc.abstractmethod
    def to_async(self) -> 'AsyncBaseNode':
        pass

    @abc.abstractmethod
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Implements the processing logic for the node"""

    @property
    def name(self) -> str | None:
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        if not isinstance(name, str):
            raise TypeError(f"name must be instance of {str}")
        elif not name.isidentifier():
            raise ValueError(f"{name!r} is not a valid name")
        self.__name = name

    @property
    def parent(self) -> 'BaseNode' | None:
        return self.__parent

    @parent.setter
    def parent(self, parent: 'BaseNode') -> None:
        if not isinstance(parent, BaseNode):
            raise TypeError(f"parent should be an instance of {self.__class__}")
        self.__parent = parent

    @parent.deleter
    def parent(self) -> None:
        self.__parent = None

    @property
    def core(self) -> T:
        return self.__core

    @property
    def root(self) -> 'BaseNode' | None:
        root = self.parent
        while root is not None and (parent := root.parent) is not None:
            root = parent
        return root

    def _rep_prep(self, reporter: Reporter | None) -> Reporter:
        if reporter is None:
            return Reporter(self.name, self.severity)
        if not isinstance(reporter, Reporter):
            raise TypeError(f"reporter must be an instance of {Reporter.__qualname__}")
        return reporter(self.name, self.severity)


class AsyncBaseNode(BaseNode[T, Input, Coroutine[None, None, Output]], Generic[T, Input, Output]):
    """Base class for all fastchain asynchronous nodes"""
    async def __call__(self, arg: Input, /, reporter: Reporter | None = None) -> Output | None:
        reporter = self._rep_prep(reporter)
        return await self.process(arg, reporter)

    def to_async(self) -> 'AsyncBaseNode':
        return self.copy()

    @abc.abstractmethod
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Implements the processing logic for the async node"""


class Node(BaseNode[Callable[[Input], Output], Input, Output], Generic[Input, Output]):
    def to_async(self) -> 'AsyncNode':
        return AsyncNode(asyncify(self.__core))

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        with reporter(self.name, self.severity, data=arg):
            return self.__core(arg)


class AsyncNode(AsyncBaseNode[Callable[[Input], Coroutine[None, None, Output]], Input, Output], Generic[Input, Output]):
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        with reporter(self.name, self.severity, data=arg):
            return await self.__core(arg)


class CollectionMixin:
    _core: list

    def __bool__(self) -> bool:
        return bool(self._core)


class Chain(BaseNode[list[BaseNode], Input, Output], CollectionMixin, Generic[Input, Output]):
    def to_async(self) -> 'AsyncChain[Input, Output]':
        return AsyncChain([node.to_async() for node in self.__core])

    def process(self, arg: Any, reporter: Reporter) -> Feedback[Output]:
        for node in self.__core:
            res = node.process(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(AsyncBaseNode[list[AsyncBaseNode], Input, Output], CollectionMixin, Generic[Input, Output]):
    async def process(self, arg: Any, reporter: Reporter) -> Feedback[Output]:
        for node in self.__core:
            res = await node.process(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class Loop(BaseNode[BaseNode[Input, Output], Iterable[Input], list[Output]], Generic[Input, Output]):
    def to_async(self) -> 'AsyncLoop[Input, Output]':
        return AsyncLoop(self.__core.to_async())

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[list[Output]]:
        return list(filter(None, (self.__core.process(arg, reporter(f'input-{i}')) for i, arg in enumerate(args))))


class AsyncLoop(AsyncBaseNode[AsyncBaseNode[Input, Output], Iterable[Input], list[Output]], Generic[Input, Output]):
    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[list[Output]]:
        results = await asyncio.gather(*[
            asyncio.create_task(self.__core.process(arg, reporter(f'input-{i}')))
            for i, arg in enumerate(args)
        ])
        return list(filter(None, results))


class Model(BaseNode[list[tuple[str, BaseNode]], Input, Output], Generic[Input, Output]):
    def to_async(self) -> 'AsyncModel[Input, Output]':
        return AsyncModel([(branch, node.to_async()) for branch, node in self.__core])

    @staticmethod
    def _convert(results: Iterable[tuple[str, Any]]) -> T:
        raise NotImplementedError

    def process(self, arg: Input, reporter: Reporter) -> T:
        return self._convert(
            (branch, result)
            for branch, result, severity
            in ((branch, node.process(arg, reporter(branch)), node.severity) for branch, node in self.__core)
            if not (branch is None and severity is OPTIONAL)
        )


class AsyncModel(AsyncBaseNode[list[tuple[str, AsyncBaseNode]], Input, Output], Generic[Input, Output]):
    @staticmethod
    def _convert(results: Iterable[tuple[str, Any]]) -> T:
        raise NotImplementedError

    async def process(self, arg: Input, reporter: Reporter) -> T:
        branches, severities, tasks = zip(*[
            (branch,
             node.severity,
             asyncio.create_task(node(arg, reporter(branch))))
            for branch, node in self.__core
        ])
        return self._convert(
            (branch, result)
            for branch, result, severity
            in zip(branches, await asyncio.gather(*tasks), severities, strict=True)
            if not (branch is None and severity is OPTIONAL)
        )


class DictModelMixin:
    @staticmethod
    def _convert(results: Iterable[tuple[str, Any]]) -> dict[str, Any]:
        return {branch: result for branch, result in results}


class ListModelMixin:
    @staticmethod
    def _convert(results: Iterable[str, Any]) -> list[Any]:
        return [result for _, result in results]


class ListModel(Model[Input, list[Output]], ListModelMixin, CollectionMixin, Generic[Input, Output]):
    pass


class AsyncListModel(AsyncModel[Input, list[Output]], ListModelMixin, CollectionMixin, Generic[Input, Output]):
    pass


class DictModel(Model[Input, dict[Any, Output]], DictModelMixin, CollectionMixin, Generic[Input, Output]):
    pass


class AsyncDictModel(AsyncModel[Input, dict[Any, Output]], DictModelMixin, CollectionMixin, Generic[Input, Output]):
    pass
