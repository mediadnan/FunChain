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

from ._util import get_name, asyncify, get_varname
from .reporter import Reporter, Severity, OPTIONAL, INHERIT

T = TypeVar('T')
Input = TypeVar('Input')
Output = TypeVar('Output')
Output2 = TypeVar('Output2')

Chainable: TypeAlias = ('BaseNode[Input, Output]' |
                        Callable[[Input], Output] |
                        dict[Any, 'Chainable[Input, Output]'] |
                        list['Chainable[Input, Output]'])


Feedback: TypeAlias = Output | None


class BaseNode(Generic[Input, Output]):
    """Base class for all fastchain nodes"""
    _core: T
    name: str
    severity: Severity
    root: 'BaseNode' | None

    def __init__(
            self,
            core: T, /,
            name: str | None = None,
            severity: Severity = INHERIT,
            root: 'BaseNode' | None = None
    ) -> None:
        self.name = name
        self.root = root
        self._core = core
        self.severity = severity

    def __call__(self, arg: Input, /, reporter: Reporter | None = None) -> Output | None:
        reporter = self._rep_prep(reporter)
        return self.process(arg, reporter)

    def __copy__(self) -> Self:
        return self.__class__(self._core, self.name, self.severity, self.root)

    @abc.abstractmethod
    def to_async(self) -> 'AsyncBaseNode':
        pass

    @abc.abstractmethod
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Implements the processing logic for the node"""

    def _rep_prep(self, reporter: Reporter | None) -> Reporter:
        if reporter is None:
            return Reporter(self.name, self.severity)
        if not isinstance(reporter, Reporter):
            raise TypeError(f"reporter must be an instance of {Reporter.__qualname__}")
        return reporter(self.name, self.severity)


class AsyncBaseNode(BaseNode[Input, Coroutine[None, None, Output]], Generic[Input, Output]):
    """Base class for all fastchain asynchronous nodes"""
    async def __call__(self, arg: Input, /, reporter: Reporter | None = None) -> Output | None:
        reporter = self._rep_prep(reporter)
        return await self.process(arg, reporter)

    def to_async(self) -> 'AsyncBaseNode':
        return self.__copy__()

    @abc.abstractmethod
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Implements the processing logic for the async node"""


class Node(BaseNode[Input, Output], Generic[Input, Output]):
    _core: Callable[[Input], Output]

    def to_async(self) -> 'AsyncNode':
        return AsyncNode(
            asyncify(self._core),
            name=self.name,
            severity=self.severity,
            root=self.root
        )

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        with reporter(self.name, self.severity, data=arg):
            return self._core(arg)


class AsyncNode(AsyncBaseNode[Input, Output], Generic[Input, Output]):
    _core: Callable[[Input], Coroutine[None, None, Output]]

    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        with reporter(self.name, self.severity, data=arg):
            return await self._core(arg)


class Chain(BaseNode):
    _core: list[BaseNode]

    def to_async(self) -> 'AsyncChain':
        return AsyncChain(
            [node.to_async() for node in self._core],
            name=self.name,
            severity=self.severity,
            root=self.root
        )

    def process(self, arg: Any, reporter: Reporter) -> Feedback[Output]:
        for node in self._core:
            res = node.process(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(AsyncBaseNode):
    _core: list[AsyncBaseNode]

    async def process(self, arg: Any, reporter: Reporter) -> Feedback[Output]:
        for node in self._core:
            res = await node.process(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class Loop(BaseNode[Iterable[Input], list[Output]], Generic[Input, Output]):
    _core: BaseNode[Input, Output]

    def to_async(self) -> 'AsyncLoop':
        return AsyncLoop(
            self._core.to_async(),
            name=self.name,
            severity=self.severity,
            root=self.root
        )

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[list[Output]]:
        return list(filter(None, (self._core.process(arg, reporter(f'input-{i}')) for i, arg in enumerate(args))))


class AsyncLoop(AsyncBaseNode[Iterable[Input], list[Output]], Generic[Input, Output]):
    _core: AsyncBaseNode[Input, Output]

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[list[Output]]:
        results = await asyncio.gather(*[
            asyncio.create_task(self._core.process(arg, reporter(f'input-{i}')))
            for i, arg in enumerate(args)
        ])
        return list(filter(None, results))


class Model(BaseNode):
    _core: list[tuple[str, BaseNode]]

    def to_async(self) -> 'AsyncModel':
        return AsyncModel(
            [(branch, node.to_async()) for branch, node in self._core],
            name=self.name,
            severity=self.severity,
            root=self.root
        )

    @staticmethod
    def _convert(results: Iterable[tuple[str, Any]]) -> T:
        raise NotImplementedError

    def process(self, arg: Input, reporter: Reporter) -> T:
        return self._convert(
            (branch, result)
            for branch, result, severity
            in ((branch, node.process(arg, reporter(branch)), node.severity) for branch, node in self._core)
            if not (branch is None and severity is OPTIONAL)
        )


class AsyncModel(AsyncBaseNode):
    _core: list[tuple[str, AsyncBaseNode]]

    @staticmethod
    def _convert(results: Iterable[tuple[str, Any]]) -> T:
        raise NotImplementedError

    async def process(self, arg: Input, reporter: Reporter) -> T:
        branches, severities, tasks = zip(*[
            (branch,
             node.severity,
             asyncio.create_task(node(arg, reporter(branch))))
            for branch, node in self._core
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


class ListModel(Model[Input, list[Output]], ListModelMixin, Generic[Input, Output]):
    pass


class AsyncListModel(AsyncModel[Input, list[Output]], ListModelMixin, Generic[Input, Output]):
    pass


class DictModel(Model[Input, dict[Any, Output]], DictModelMixin, Generic[Input, Output]):
    pass


class AsyncDictModel(AsyncModel[Input, dict[Any, Output]], DictModelMixin, Generic[Input, Output]):
    pass
