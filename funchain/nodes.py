import asyncio
import functools
from abc import ABC, abstractmethod, ABCMeta
from enum import Enum
from typing import (TypeVar,
                    TypeAlias,
                    Union,
                    Callable,
                    Coroutine,
                    Self,
                    Iterable)
from failures import Reporter

from ._tools import asyncify, validate_name


T = TypeVar('T')
U = TypeVar('U')
Feedback: TypeAlias = tuple[bool, T]
SingleInputFunction: TypeAlias = Callable[[T], U]
SingleInputAsyncFunction: TypeAlias = Callable[[T], Coroutine[None, None, U]]


class Severity(Enum):
    """Specifies the behavior in case of failure"""
    OPTIONAL = -1   # Ignores the node in case of failure
    NORMAL = 0      # Reports the failure and returns None as alternative
    REQUIRED = 1    # Breaks the entire chain execution and reports


class Failed(Exception):
    """This error gets raised by a required node that failed; to stop the cascading execution"""


class BaseNode(ABC):
    """Base class for all FunChain nodes"""
    __slots__ = ('__severity',)
    __severity: Severity

    def __init__(self) -> None:
        self.severity = Severity.NORMAL

    def __or__(self, other: 'BaseNode') -> 'Chain':
        return Chain([self]) | other

    def __mul__(self, other: 'BaseNode') -> 'Chain':
        return Chain([self]) * other

    def __call__(self, arg, /, reporter: Reporter = None):
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
    def process(self, arg, reporter: Union[Reporter, type[Reporter]]) -> Feedback: ...

    @abstractmethod
    def to_async(self) -> 'AsyncBaseNode':
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

    def rn(self, name: str) -> 'BaseNode':
        """Returns a clone of the current node with the new name"""
        return SemanticNode(self, name)


class AsyncBaseNode(BaseNode):
    def __or__(self, other: BaseNode) -> 'AsyncChain':
        return AsyncChain([self]) | other

    def __mul__(self, other: BaseNode) -> 'AsyncChain':
        return AsyncChain([self]) * other

    def to_async(self) -> Self:
        """Returns the current node"""
        return self

    def rn(self, name: str) -> 'AsyncBaseNode':
        return AsyncSemanticNode(self, name)

    @abstractmethod
    async def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback: ...

    async def __call__(self, arg, /, reporter: Reporter = None):
        try:
            return (await self.process(arg, self._process_reporter(reporter)))[1]
        except Failed:
            return


class Node(BaseNode):
    __slots__ = ('__fun', '__name')
    __fun: SingleInputFunction
    __name: str

    def __init__(self, fun: SingleInputFunction, name: str = None) -> None:
        super().__init__()
        self.__fun = fun
        self.__name = name

    @property
    def fun(self) -> SingleInputFunction:
        """Gets the internal function"""
        return self.__fun

    @property
    def name(self) -> str:
        """Gets the name of the leaf node (function)"""
        return self.__name

    def to_async(self) -> 'AsyncNode':
        return AsyncNode(asyncify(self.__fun), self.__name)

    def partial(self, *args, **kwargs) -> Self:
        """Clones the node and partially applies the arguments"""
        func = self.__fun
        while isinstance(func, functools.partial):
            args = *func.args, *args
            kwargs = {**func.keywords, **kwargs}
            func = func.func
        return self.__class__(functools.partial(func, *args, **kwargs), self.__name)

    def rn(self, name: str) -> Self:
        """Returns a clone of the current node with the new name"""
        validate_name(name)
        return self.__class__(self.__fun, name)

    def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback:
        try:
            return True, self.__fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    def handle_failure(self, error: Exception, arg, reporter: Reporter) -> Feedback:
        """Reports the failure according to the node severity"""
        severity = self.severity
        if severity is not Severity.OPTIONAL:
            reporter(self.name).report(error, input=arg)
        if severity is Severity.REQUIRED:
            raise Failed
        return False, None


class AsyncNode(Node, AsyncBaseNode):
    fun: SingleInputAsyncFunction

    async def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback:
        try:
            return True, await self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)


class PassiveNode(BaseNode):
    """A node that returns the input as it is"""
    def process(self, arg, reporter: Union[Reporter, type[Reporter]]) -> Feedback:
        return True, arg

    def to_async(self) -> 'AsyncBaseNode':
        return AsyncPassiveNode()


class AsyncPassiveNode(PassiveNode, AsyncBaseNode):
    async def process(self, arg, reporter: Union[Reporter, type[Reporter]]) -> Feedback:
        return True, arg


class WrapperNode(BaseNode, metaclass=ABCMeta):
    __slots__ = ('__node',)
    __node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__()
        self.__node = node

    @property
    def node(self) -> BaseNode:
        """Returns the wrapped node (Read-only)"""
        return self.__node


class SemanticNode(WrapperNode):
    """This node holds the label for to be reported in case of failure"""
    __slots__ = ('__name',)
    __name: str

    def __init__(self, node: BaseNode, /, name: str) -> None:
        super().__init__(node)
        self.name = name

    def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback:
        return self.node.process(arg, reporter(self.name))

    @property
    def name(self) -> str:
        """Gets the label of the node (Read-only)"""
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        validate_name(name)
        self.__name = name

    def rn(self, name: str) -> Self:
        return self.__class__(self.node, name)

    def to_async(self) -> 'AsyncSemanticNode':
        return AsyncSemanticNode(self.node.to_async(), self.name)


class AsyncSemanticNode(SemanticNode, AsyncBaseNode):
    node: AsyncBaseNode

    async def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback:
        return await self.node.process(arg, reporter(self.name))


class Chain(BaseNode):
    __slots__ = '__nodes',
    __nodes: list[BaseNode]

    def __init__(self, nodes: list[BaseNode], /) -> None:
        super().__init__()
        self.__nodes = list(nodes)

    def __or__(self, other: BaseNode) -> 'Chain':
        if not isinstance(other, BaseNode):
            raise TypeError("Chained node must be instance of failures.BaseNode")
        if isinstance(other, AsyncBaseNode):
            return self.to_async() | other
        return Chain([*self.__nodes, other])

    def __mul__(self, other: BaseNode) -> 'Chain':
        if not isinstance(other, BaseNode):
            raise TypeError("Chained node must be instance of failures.BaseNode")
        if isinstance(other, AsyncBaseNode):
            return self.to_async() * other
        return Chain([*self.__nodes, Loop(other)])

    @property
    def nodes(self) -> list[BaseNode]:
        """Gets nodes (Read-only / Mutable)"""
        return self.__nodes

    def to_async(self) -> 'AsyncChain':
        return AsyncChain([node.to_async() for node in self.nodes])

    def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback:
        for node in self.nodes:
            success, res = node.process(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


class AsyncChain(Chain, AsyncBaseNode):
    nodes: list[AsyncBaseNode]

    def __or__(self, other: BaseNode | AsyncBaseNode) -> 'AsyncChain':
        return AsyncChain([*self.nodes, other.to_async()])

    def __mul__(self, other) -> 'AsyncChain':
        return AsyncChain([*self.nodes, AsyncLoop(other.to_async())])

    async def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback:
        for node in self.nodes:
            success, res = await node.process(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


class Loop(WrapperNode):
    """Wrapper node that processes each element of the input through the wrapped node and returns a list of results"""
    def to_async(self) -> 'AsyncLoop':
        return AsyncLoop(self.node.to_async())

    def process(self, args: Iterable, reporter: Reporter) -> Feedback:
        if not args:
            return True, []
        successes: set[bool] = set()
        results = []
        node = self.node
        for arg in args:
            success, res = node.process(arg, reporter)
            successes.add(success)
            results.append(res)
        return any(successes), results


class AsyncLoop(Loop, AsyncBaseNode):
    """A node that processes each element of the input asynchronously through the wrapped node and returns a list of
    results"""
    node: AsyncBaseNode

    async def process(self, args: Iterable, reporter: Reporter) -> Feedback:
        if not args:
            return True, []
        node = self.node
        jobs = await asyncio.gather(*(asyncio.create_task(node.process(arg, reporter)) for arg in args))
        successes, results = zip(*jobs)
        return any(successes), results


class Group(BaseNode):
    """A node that processes the input through multiple branches and returns a list as a result"""
    __slots__ = ('__nodes', '__severities')
    __severities: tuple[Severity, ...]
    __nodes: tuple[BaseNode, ...]

    def __init__(self, nodes: Iterable[BaseNode], /):
        super().__init__()
        self.__severities = tuple(node.severity for node in nodes)
        self.__nodes = tuple(nodes)

    def to_async(self) -> 'AsyncGroup':
        return AsyncGroup([node.to_async() for node in self.__nodes])

    @property
    def nodes(self) -> tuple[BaseNode, ...]:
        """Gets nodes (Read-only / Mutable)"""
        return self.__nodes

    @property
    def severities(self) -> tuple[Severity, ...]:
        """Gets severities (Read-only / Mutable)"""
        return self.__severities

    def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback[list]:
        successes, results = zip(*(node.process(arg, reporter) for node in self.nodes))
        _results = []
        for success, result, severity in zip(successes, results, self.severities, strict=True):
            if not success:
                if severity is Severity.OPTIONAL:
                    continue
                if severity is Severity.REQUIRED:
                    raise Failed
            _results.append(result)
        return any(successes) if _results else True, _results


class AsyncGroup(Group, AsyncBaseNode):
    """A node that processes the input asynchronously through multiple branches and returns a list as a result"""
    nodes: tuple[AsyncBaseNode, ...]

    async def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback[list]:
        successes, results = zip(*(
            await asyncio.gather(*(asyncio.create_task(node.process(arg, reporter)) for node in self.nodes))
        ))
        _results = []
        for success, result, severity in zip(successes, results, self.severities, strict=True):
            if not success:
                if severity is Severity.OPTIONAL:
                    continue
                if severity is Severity.REQUIRED:
                    raise Failed
            _results.append(result)
        return any(successes) if _results else True, _results


class DictGroup(Group):
    """A node that processes the input through multiple branches and returns a dictionary as a result"""
    __slots__ = ('__branches',)
    __branches: tuple[str, ...]

    def __init__(self, nodes: Iterable[BaseNode], branches: Iterable[str], /):
        super().__init__(nodes)
        self.__branches = tuple(branches)

    @property
    def branches(self) -> tuple[str, ...]:
        """Gets branches (Read-only / Mutable)"""
        return self.__branches

    def to_async(self) -> 'AsyncDictGroup':
        return AsyncDictGroup([node.to_async() for node in self.nodes], self.branches)

    def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback[dict]:
        successes, results = zip(*(node.process(arg, reporter) for node in self.nodes))
        _results = {}
        for branch, success, result, severity in zip(self.branches, successes, results, self.severities, strict=True):
            if not success:
                if severity is Severity.OPTIONAL:
                    continue
                if severity is Severity.REQUIRED:
                    raise Failed
            _results[branch] = result
        return any(successes) if _results else True, _results


class AsyncDictGroup(DictGroup, AsyncBaseNode):
    """A node that processes the input asynchronously through multiple branches and returns a dictionary as a result"""
    nodes: tuple[AsyncBaseNode, ...]

    async def process(self, arg, reporter: Reporter | type[Reporter]) -> Feedback[dict]:
        successes, results = zip(*(
            await asyncio.gather(*(asyncio.create_task(node.process(arg, reporter)) for node in self.nodes))
        ))
        _results = {}
        for branch, success, result, severity in zip(self.branches, successes, results, self.severities, strict=True):
            if not success:
                if severity is Severity.OPTIONAL:
                    continue
                if severity is Severity.REQUIRED:
                    raise Failed
            _results[branch] = result
        return any(successes) if _results else True, _results
