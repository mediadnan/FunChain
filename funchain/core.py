import asyncio
import functools
from abc import ABC, abstractmethod
from enum import Enum
from typing import (TypeVar,
                    TypeAlias,
                    Callable,
                    Coroutine,
                    Self,
                    Iterable,
                    Any, overload, )
from failures import Reporter

from ._tools import validate_name, is_async, get_function_name

T = TypeVar('T')
U = TypeVar('U')
Feedback: TypeAlias = tuple[bool, T]
SingleInputFunction: TypeAlias = Callable[[T], U]
SingleInputAsyncFunction: TypeAlias = Callable[[T], Coroutine[None, None, U]]


class Failed(Exception):
    """This error gets raised by a required node that failed; to stop the cascading execution"""


class Severity(Enum):
    """Specifies the behavior in case of failure"""
    OPTIONAL = -1  # Ignores the node in case of failure
    NORMAL = 0  # Reports the failure and returns None as alternative
    REQUIRED = 1  # Breaks the entire chain execution and reports


class BaseNode(ABC):
    """Base class for all FunChain nodes"""
    __slots__ = ('severity',)
    severity: Severity

    def __init__(self) -> None:
        self.severity = Severity.NORMAL

    @property
    @abstractmethod
    def is_async(self) -> bool: ...

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

    def __call__(self, arg, /, reporter: Reporter = None):
        if not (reporter is None or isinstance(reporter, Reporter)):
            raise TypeError("reporter must be instance of failures.Reporter")
        return (_async_caller if self.is_async else _caller)(self, arg, reporter)

    def __add__(self, other):
        return chain(self, other)

    def __iadd__(self, other):
        return chain(other, self)

    def __mul__(self, other):
        return chain(self, loop(other))

    def __imul__(self, other):
        return chain(other, loop(self))


class Node(BaseNode):
    __slots__ = ('fun', 'name')
    fun: SingleInputFunction
    name: str
    is_async = False

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
    is_async = True

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        try:
            return True, await self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    def proc(self, arg, reporter: Reporter | None) -> Feedback:
        return asyncio.run(self.aproc(arg, reporter))


class PassiveNode(BaseNode):
    """A node that returns the input as it is"""
    is_async = False

    def proc(self, arg, /, reporter: Reporter | None) -> Feedback:
        return True, arg

    async def aproc(self, arg, /, reporter: Reporter | None) -> Feedback:
        return True, arg

    def rn(self, name: str) -> 'PassiveNode':
        return self


class WrapperNode(BaseNode, ABC):
    __slots__ = ('node',)
    node: BaseNode

    def __init__(self, node: BaseNode, /) -> None:
        super().__init__()
        self.node = node

    @property
    def is_async(self) -> bool:
        return self.node.is_async


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
    __slots__ = ('_nodes', '__is_async')
    _nodes: tuple[BaseNode, ...]
    __is_async: bool

    def __init__(self, nodes: Iterable[BaseNode], /) -> None:
        super().__init__()
        self._nodes = tuple(nodes)
        self.__is_async = any(node.is_async for node in self._nodes)

    @property
    def is_async(self) -> bool:
        return self.__is_async


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


def _caller(node: 'BaseNode', arg, reporter: Reporter | None):
    try:
        return node.proc(arg, reporter)[1]
    except Failed:
        return


async def _async_caller(node: 'BaseNode', arg, reporter: Reporter | None):
    try:
        return (await node.aproc(arg, reporter))[1]
    except Failed:
        return


PASS = PassiveNode()


def loop(*nodes) -> BaseNode:
    """Builds a node that applies to each element of the input"""
    node = _build(nodes)
    if node is PASS:
        return node
    return Loop(node)


def optional(*nodes) -> BaseNode:
    """Builds a node that will be ignored in case of failures"""
    node = _build(nodes)
    if node is PASS:
        return node
    node.severity = Severity.OPTIONAL
    return node


def required(*nodes) -> BaseNode:
    """Builds a node that stops the entire chain in case of failures"""
    node = _build(nodes)
    if node is PASS:
        return node
    node.severity = Severity.REQUIRED
    return node


def static(obj, /) -> Node:
    """Builds a node that returns that same object regardless of the input"""
    _name = str(obj)
    if len(_name) > 20:
        # Shorten long names
        _name = _name[: 8] + '-' + _name[len(_name) - 7:]
    try:
        validate_name(_name)
        _name = f'static_node({_name})'
    except (ValueError, TypeError):
        _name = 'static_node'
    return _build_node(lambda _: obj, _name)


def chain(*nodes, name: str | None = None) -> BaseNode:
    """Composes nodes in a sequential chain"""
    return _build(nodes, name)


def _build(obj: Any = ..., /, name: str = None) -> BaseNode:
    if isinstance(obj, BaseNode):
        return obj.rn(name) if name else obj
    if callable(obj):
        return _build_node(obj, name)
    elif isinstance(obj, tuple):
        return _build_chain(obj, name)
    elif isinstance(obj, dict):
        return _build_node_dict(obj, name)
    elif isinstance(obj, list):
        return _build_node_list(obj, name)
    elif obj is ...:
        return PASS
    return static(obj)


def _build_node(fun: SingleInputFunction, /, name: str | None = None) -> Node:
    """Builds a leaf node from a function"""
    if name is None:
        name = get_function_name(fun)
    else:
        validate_name(name)
    return (AsyncNode if is_async(fun) else Node)(fun, name)


def _build_node_list(struct: list[Any], /, name: str | None = None) -> BaseNode:
    """Builds a branched node dict"""
    _nodes = tuple(map(_build, struct))
    node: BaseNode = NodeList(_nodes)
    if name:
        node = node.rn(name)
    return node


def _build_node_dict(struct: dict[str, Any], /, name: str | None = None) -> BaseNode:
    """Builds a branched node list"""
    _branches = tuple(map(str, struct.keys()))
    _nodes = tuple(map(_build, struct.values()))
    node: BaseNode = NodeDict(_nodes, _branches)
    if name:
        node = node.rn(name)
    return node


def _build_chain(nodes: tuple, /, name: str | None = None) -> BaseNode:
    """Builds a sequential chain of nodes"""
    if not nodes:
        return PASS
    if len(nodes) == 1:
        return _build(nodes[0], name)
    _nodes: list[BaseNode] = list(filter(lambda x: not isinstance(x, PassiveNode), map(_build, nodes)))
    node: BaseNode = NodeChain(_nodes)
    if name:
        node = node.rn(name)
    return node


@overload
def _node(fun: SingleInputAsyncFunction, /, name: str | None = ...) -> AsyncNode: ...
@overload
def _node(fun: SingleInputFunction, /, name: str | None = ...) -> Node: ...


def _node(fun: SingleInputFunction, /, name: str | None = None) -> Node:
    if not callable(fun):
        raise TypeError("The node function must be callable")
    return _build_node(fun, name)
