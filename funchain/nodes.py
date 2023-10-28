import asyncio
import functools
from abc import ABC, abstractmethod
from enum import Enum
from typing import (TypeVar,
                    TypeAlias,
                    Callable,
                    Coroutine,
                    Self,
                    Iterable, overload, Any, )
from failures import Reporter

from ._tools import validate_name, is_async

T = TypeVar('T')
U = TypeVar('U')
Feedback: TypeAlias = tuple[bool, T]
SingleInputFunction: TypeAlias = Callable[[T], U]
SingleInputAsyncFunction: TypeAlias = Callable[[T], Coroutine[None, None, U]]


class Severity(Enum):
    """Specifies the behavior in case of failure"""
    OPTIONAL = -1  # Ignores the node in case of failure
    NORMAL = 0  # Reports the failure and returns None as alternative
    REQUIRED = 1  # Breaks the entire chain execution and reports


class Failed(Exception):
    """This error gets raised by a required node that failed; to stop the cascading execution"""


def _validate_reporter(rep: Reporter | None) -> None:
    """Validates the reporter's type"""
    if rep is None or isinstance(rep, Reporter):
        return
    raise TypeError("reporter must be instance of failures.Reporter or None")


class Runner:
    __slots__ = ('__node', 'is_async')
    __node: 'BaseNode'
    is_async: bool

    def __init__(self, node: 'BaseNode', /) -> None:
        self. __node = node

    @property
    def node(self) -> 'BaseNode':
        """Gets the internal node (Read-only)"""
        return self.__node

    @overload
    def __add__(self, other: 'AsyncRunner') -> 'AsyncRunner': ...
    @overload
    def __add__(self, other: 'Runner') -> 'Runner': ...

    def __add__(self, other):
        if not isinstance(other, Runner):
            raise TypeError(f"A {self.__class__.__name__} can only be piped \
            to a {Runner.__name__} object")
        node = NodeChain([self.node, other.node])
        if isinstance(self, AsyncRunner) or isinstance(other, AsyncRunner):
            return AsyncRunner(node)
        return Runner(node)

    def __call__(self, inp, /, reporter: Reporter | None = None):
        """
        Processes arg and returns the result

        :param inp: The input to be processed
        :param reporter: Used to report any nested failure (optional)
        :type reporter: Reporter
        :returns: The final result of processing or None in case of failure
        """
        _validate_reporter(reporter)
        try:
            return self.node.proc(inp, reporter)[1]
        except Failed:
            return


class AsyncRunner(Runner):
    async def __call__(self, inp, /, reporter: Reporter | None = None):
        _validate_reporter(reporter)
        try:
            return (await self.node.aproc(inp, reporter))[1]
        except Failed:
            return

    # def __add__(self, other: 'Runner') -> 'AsyncRunner':
    #     passCoroutine


class BaseNode(ABC):
    """Base class for all FunChain nodes"""
    __slots__ = ('severity',)
    severity: Severity

    def __init__(self) -> None:
        self.severity = Severity.NORMAL

    @abstractmethod
    def proc(self, arg, /, reporter: Reporter | None) -> Feedback:
        """Processes the argument and returns a success indicator (bool) \
        together with the result, reporting any failures if a reporter is passed."""

    @abstractmethod
    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        """Processes the input asynchronously and returns a success \
        indicator (bool) with the result, reporting any failures if a reporter is passed"""

    def rn(self, name: str) -> 'BaseNode':
        """Returns a labeled version of the current node"""
        return SemanticNode(self, name)


class Node(BaseNode):
    __slots__ = ('fun', 'name')
    fun: SingleInputFunction
    name: str

    def __init__(self, fun: SingleInputFunction, name: str) -> None:
        super().__init__()
        self.fun = fun
        self.name = name

    def partial(self, *args, **kwargs) -> Self:
        """Clones the node and partially applies the arguments"""
        func = self.fun
        while isinstance(func, functools.partial):
            args = *func.args, *args
            kwargs = {**func.keywords, **kwargs}
            func = func.func
        return self.__class__(functools.partial(func, *args, **kwargs), self.name)

    def rn(self, name: str) -> Self:
        """Returns a clone of the current node with the new name"""
        validate_name(name)
        return self.__class__(self.fun, name)

    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        try:
            return True, self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        # loop = asyncio.get_event_loop()
        # return await loop.run_in_executor(None, lambda: self.proc(arg, reporter))
        return self.proc(arg, reporter)

    def handle_failure(self, error: Exception, arg, reporter: Reporter | None) -> Feedback:
        """Reports the failure according to the node severity"""
        severity = self.severity
        if not (severity is Severity.OPTIONAL or reporter is None):
            reporter(self.name).report(error, input=arg)
        if severity is Severity.REQUIRED:
            raise Failed
        return False, None


class AsyncNode(Node):
    fun: SingleInputAsyncFunction

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        try:
            return True, await self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        return asyncio.run(self.aproc(arg, reporter))


class PassiveNode(BaseNode):
    """A node that returns the input as it is"""

    def proc(self, arg, /, reporter: Reporter | None) -> Feedback:
        return True, arg

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        return True, arg


class WrapperNode(BaseNode, ABC):
    __slots__ = ('node',)
    node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__()
        self.node = node


class SemanticNode(WrapperNode):
    """This node holds the label for to be reported in case of failure"""
    __slots__ = ('__name',)
    __name: str

    def __init__(self, node: BaseNode, /, name: str) -> None:
        super().__init__(node)
        self.name = name

    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        return self.node.proc(arg, reporter and reporter(self.name))

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        return await self.node.aproc(arg, reporter and reporter(self.name))

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


class Loop(WrapperNode):
    """Wrapper node that processes each element of the input through the wrapped node and returns a list of results"""

    def proc(self, args: Iterable, /, reporter: Reporter | None) -> Feedback:
        if not args:
            return True, []
        successes: set[bool] = set()
        results = []
        node = self.node
        for arg in args:
            success, res = node.proc(arg, reporter)
            successes.add(success)
            results.append(res)
        return any(successes), results

    async def aproc(self, args: Iterable, /, reporter: Reporter | None) -> Feedback:
        if not args:
            return True, []
        node = self.node
        jobs = await asyncio.gather(*(asyncio.create_task(node.aproc(arg, reporter)) for arg in args))
        successes, results = zip(*jobs)
        return any(successes), results


class NodeGroup(BaseNode, ABC):
    __slots__ = '_nodes',
    _nodes: tuple[BaseNode, ...]

    def __init__(self, nodes: Iterable[BaseNode], /) -> None:
        super().__init__()
        self._nodes = tuple(nodes)


class NodeChain(NodeGroup):
    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        for node in self._nodes:
            success, res = node.proc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        for node in self._nodes:
            success, res = await node.aproc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg


class NodeList(NodeGroup):
    """A node that processes the input through multiple branches and returns a list as a result"""
    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        successes: set[bool] = set()
        results = []
        for node in self._nodes:
            success, result = node.proc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                if node.severity is Severity.REQUIRED:
                    raise Failed
            successes.add(success)
            results.append(result)
        success = (not results) or any(successes)
        return success, results

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        successes: set[bool] = set()
        results = []
        for (success, result), node in zip(
                await asyncio.gather(
                    *(asyncio.create_task(node.aproc(arg, reporter)) for node in self._nodes)
                ),
                self._nodes,
                strict=True
        ):
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                if node.severity is Severity.REQUIRED:
                    raise Failed
            successes.add(success)
            results.append(result)
        success = (not results) or any(successes)
        return success, results


class NodeDict(NodeList):
    """A node that processes the input through multiple branches and returns a dictionary as a result"""
    __slots__ = ('_branches',)
    _branches: tuple[str, ...]

    def __init__(self, nodes: Iterable[BaseNode], branches: Iterable[str], /):
        super().__init__(nodes)
        self._branches = tuple(branches)

    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        successes: set[bool] = set()
        results = {}
        for branch, node in zip(self._branches, self._nodes):
            success, result = node.proc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                if node.severity is Severity.REQUIRED:
                    raise Failed
            successes.add(success)
            results[branch] = result
        success = (not results) or any(successes)
        return success, results

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        successes: set[bool] = set()
        results = {}
        for (success, result), node, branch in zip(
                await asyncio.gather(
                    *(asyncio.create_task(node.aproc(arg, reporter)) for node in self._nodes)
                ),
                self._nodes,
                self._branches,
                strict=True
        ):
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                if node.severity is Severity.REQUIRED:
                    raise Failed
            successes.add(success)
            results[branch] = result
        success = (not results) or any(successes)
        return success, results


PASSIVE = PassiveNode()


def _build(obj: Any = PASSIVE, /, name: str = None) -> tuple[bool, BaseNode]:
    _is_async: bool
    if isinstance(obj, Runner):
        return _build(obj.node, name)
    if isinstance(obj, BaseNode):
        _is_async = isinstance(obj, AsyncNode)
        if name:
            return _is_async, obj.rn(name)
        return _is_async, obj
    if callable(obj):
        _is_async = is_async(obj)


