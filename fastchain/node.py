from __future__ import annotations
import abc
import asyncio
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    Generic,
    TypeVar,
    Callable,
    Iterable,
    Coroutine,
    Literal,
    TypeAlias,
    overload,
)

from ._util import asyncify, get_varname, get_name
from .reporter import Reporter, Severity, OPTIONAL, INHERIT



T = TypeVar('T')
Input = TypeVar('Input')
Output = TypeVar('Output')
Output2 = TypeVar('Output2')

if TYPE_CHECKING:
    Feedback: TypeAlias = Output | None
    AsyncCallable: TypeAlias = Callable[[Input], Coroutine[None, None, Output]]

    Chainable: TypeAlias = ('BaseNode[Input, Output]' |
                        Callable[[Input], Output] |
                        dict[Any, 'Chainable[Input, Output]'] |
                        list['Chainable[Input, Output]'] |
                        tuple['Chainable', ...])


    AsyncChainable: TypeAlias = ('AsyncBaseNode[Input, Output]' |
                                 AsyncCallable[Input, Output] |
                                 Callable[[Input], Output] |
                                 dict[Any, 'AsyncChainable[Input, Output]'] |
                                 list['AsyncChainable[Input, Output]'] |
                                 tuple['AsyncChainable', ...])




# Node type definitions ##################################################################

class BaseNode(Generic[T, Input, Output]):
    """Base class for all fastchain nodes"""
    _core: T
    name: str
    severity: Severity
    parent: BaseNode | None

    def __init__(self, core: T, /) -> None:
        self._core = core
        self.severity = INHERIT
        self.__name: str | None = None
        self.__parent: BaseNode | None = None

    def __call__(self, arg: Input, /, reporter: Reporter | None = None) -> Output | None:
        reporter = self._rep_prep(reporter)
        return self.process(arg, reporter)

    def copy(self) -> Self:
        new = self.__class__(self._core)
        new.__dict__.update(self.__dict__)
        return new

    def __or__(self):
        pass

    def __mul__(self):
        pass

    @abc.abstractmethod
    def to_async(self) -> AsyncBaseNode:
        pass

    @abc.abstractmethod
    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Implements the processing logic for the node"""

    @property
    def name(self) -> str | None:
        return self.__name

    @name.setter
    def name(self, name: str | None) -> None:
        if name is None:
            return
        elif not isinstance(name, str):
            raise TypeError(f"name must be instance of {str}")
        elif not True:
            # TODO: validate name
            raise ValueError(f"{name!r} is not a valid name")
        self.__name = name

    @property
    def parent(self) -> BaseNode | None:
        return self.__parent

    @parent.setter
    def parent(self, parent: BaseNode) -> None:
        if not isinstance(parent, BaseNode):
            raise TypeError(f"parent should be an instance of {self.__class__}")
        self.__parent = parent

    @parent.deleter
    def parent(self) -> None:
        self.__parent = None

    @property
    def core(self) -> T:
        return self._core

    @property
    def root(self) -> BaseNode | None:
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

    def to_async(self) -> AsyncBaseNode:
        return self.copy()

    @abc.abstractmethod
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        """Implements the processing logic for the async node"""


class Node(BaseNode[Callable[[Input], Output], Input, Output], Generic[Input, Output]):
    def to_async(self) -> AsyncNode:
        return AsyncNode(asyncify(self._core))

    def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        with reporter(self.name, self.severity, data=arg):
            return self._core(arg)


class AsyncNode(AsyncBaseNode[AsyncCallable[Input, Output], Input, Output], Generic[Input, Output]):
    async def process(self, arg: Input, reporter: Reporter) -> Feedback[Output]:
        with reporter(self.name, self.severity, data=arg):
            return await self._core(arg)


class CollectionMixin:
    _core: list

    def __bool__(self) -> bool:
        return bool(self._core)


class Chain(BaseNode[list[BaseNode], Input, Output], CollectionMixin, Generic[Input, Output]):
    def to_async(self) -> AsyncChain[Input, Output]:
        return AsyncChain([node.to_async() for node in self._core])

    def process(self, arg: Any, reporter: Reporter) -> Feedback[Output]:
        for node in self._core:
            res = node.process(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class AsyncChain(AsyncBaseNode[list[AsyncBaseNode], Input, Output], CollectionMixin, Generic[Input, Output]):
    async def process(self, arg: Any, reporter: Reporter) -> Feedback[Output]:
        for node in self._core:
            res = await node.process(arg, reporter)
            if res is None:
                if node.severity is OPTIONAL:
                    continue
                return
            arg = res
        return arg


class Loop(BaseNode[BaseNode[Any, Input, Output], Iterable[Input], list[Output]], Generic[Input, Output]):
    def to_async(self) -> AsyncLoop[Input, Output]:
        return AsyncLoop(self._core.to_async())

    def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[list[Output]]:
        return list(filter(None, (self._core.process(arg, reporter(f'input-{i}')) for i, arg in enumerate(args))))


class AsyncLoop(AsyncBaseNode[AsyncBaseNode[Any, Input, Output], Iterable[Input], list[Output]], Generic[Input, Output]):
    async def process(self, args: Iterable[Input], reporter: Reporter) -> Feedback[list[Output]]:
        results = await asyncio.gather(*[
            asyncio.create_task(self._core.process(arg, reporter(f'input-{i}')))
            for i, arg in enumerate(args)
        ])
        return list(filter(None, results))


class Model(BaseNode[list[tuple[str, BaseNode]], Input, Output], CollectionMixin, Generic[Input, Output]):
    def to_async(self) -> AsyncModel[Input, Output]:
        return AsyncModel([(branch, node.to_async()) for branch, node in self._core])

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


class AsyncModel(AsyncBaseNode[list[tuple[str, AsyncBaseNode]], Input, Output], CollectionMixin, Generic[Input, Output]):
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


def list_model_converter(results: Iterable[str, Any]) -> list[Any]:
    return [result for _, result in results]


def dict_model_converter(results: Iterable[Any, Any]) -> dict[Any, Any]:
    return {branch: result for branch, result in results}


class ListModel(Model[Input, list[Output]], CollectionMixin, Generic[Input, Output]):
    _convert = staticmethod(list_model_converter)


class AsyncListModel(AsyncModel[Input, list[Output]], CollectionMixin, Generic[Input, Output]):
    _convert = staticmethod(list_model_converter)


class DictModel(Model[Input, dict[Any, Output]], CollectionMixin, Generic[Input, Output]):
    _convert = staticmethod(dict_model_converter)


class AsyncDictModel(AsyncModel[Input, dict[Any, Output]], CollectionMixin, Generic[Input, Output]):
    _convert = staticmethod(dict_model_converter)


class PassiveNode(BaseNode[None, Input, Input], Generic[Input]):
    def __bool__(self) -> bool:
        return False

    def to_async(self) -> AsyncPassiveNode:
        return AsyncPassiveNode(None)

    def process(self, arg: Input, _: Reporter) -> Input:
        return arg


class AsyncPassiveNode(AsyncBaseNode[None, Input, Input], Generic[Input]):
    def __bool__(self) -> bool:
        return False

    async def process(self, arg: Input, _: Reporter) -> Input:
        return arg


# Node utility definitions ##############################################################

GUESS_NAME = object()


@overload
def node() -> PassiveNode[Input]: ...
@overload
def node(func: AsyncCallable[Input, Output], /, *, name: str | None = ...) -> AsyncNode[Input, Output]: ...
@overload
def node(func: Callable[[Input], Output], /, *, name: str | None = ...) -> Node[Input, Output]: ...



def node(obj: Any = Ellipsis, /, name: str | Any = GUESS_NAME):
    if obj is Ellipsis:
        node = PassiveNode(None)
    elif isinstance(obj, BaseNode):
        node = obj.copy()
    elif callable(obj):
        node = _func_node(obj, name=name)
    elif isinstance(obj, (dict, list)):
        node = _model(obj, name=name)
    else:
        raise TypeError("Unsupported type for chaining")
    

def _model(model, *, name=None):
    if isinstance(model, dict):
        branched_items = model.items()
        models = DictModel, AsyncDictModel
    elif isinstance(model, list):
        branched_items = enumerate(model)
        models = ListModel, AsyncListModel
    else:
        raise TypeError(f"model must be either an instance of {list} or {dict}")
    nodes = [
        (branch, node(item, name=str(branch)))
        for branch, item in branched_items
    ]
    nodes_are_async = set(isinstance(nd, AsyncBaseNode) for nd in nodes)
    is_async = False
    if any(nodes_are_async):
        is_async = True
        if not all(nodes_are_async):
            nodes = [nd.to_async() for nd in nodes]
    nd = models[is_async](nodes)
    nd.name = name
    return nd


def _func_node(func, *, name=None):
    pass

