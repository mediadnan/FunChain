import asyncio
import functools
import sys
from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from typing import (TypeVar,
                    Callable,
                    Coroutine,
                    Iterable,
                    Any,
                    overload,
                    Optional, )
if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self
if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias
from failures import Reporter, FailureException

from ._tools import validate_name, is_async, get_function_name

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


class BaseNode(ABC):
    """Base class for all FunChain nodes"""
    __slots__ = ('_severity',)
    _severity: Severity

    def __init__(self, *, severity: Severity = Severity.NORMAL) -> None:
        self._severity = severity

    @property
    @abstractmethod
    def is_async(self) -> bool: ...

    @abstractmethod
    def proc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        """Processes the argument and returns a success indicator (bool) \
        together with the result, reporting any failures if a reporter is passed."""

    @abstractmethod
    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        """Processes the input asynchronously and returns a success \
        indicator (bool) with the result, reporting any failures if a reporter is passed"""

    def rn(self, name: str) -> 'BaseNode':
        """Returns a labeled version of the current node"""
        return SemanticNode(self, name, severity=self.severity)

    @property
    def severity(self) -> Severity:
        """Specifies the behavior in case of failure"""
        return self._severity

    @severity.setter
    def severity(self, value: Severity) -> None:
        if not isinstance(value, Severity):
            raise TypeError("severity must be instance of failures.Severity")
        self._severity = value

    def optional(self) -> 'BaseNode':
        """Returns a clone of the current node with the optional flag"""
        node = copy(self)
        node.severity = Severity.OPTIONAL
        return node

    def required(self) -> 'BaseNode':
        """Returns a clone of the current node with the required flag"""
        node = copy(self)
        node.severity = Severity.REQUIRED
        return node

    def __call__(self, arg, /, reporter: Reporter = None):
        if not (reporter is None or isinstance(reporter, Reporter)):
            raise TypeError("reporter must be instance of failures.Reporter")
        return (_async_caller if self.is_async else _caller)(self, arg, reporter)

    def __or__(self, other):
        return chain(self, other)

    def __ior__(self, other):
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

    def __init__(self, fun: SingleInputFunction, name: str, *, severity: Severity = Severity.NORMAL) -> None:
        super().__init__(severity=severity)
        self.fun = fun
        self.name = name

    @property
    def __name__(self) -> str:
        return self.name

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
        return self.__class__(self.fun, name, severity=self.severity)

    def proc(self, arg, reporter: Optional[Reporter]) -> Feedback:
        try:
            return True, self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        # loop = asyncio.get_event_loop()
        # return await loop.run_in_executor(None, lambda: self.proc(arg, reporter))
        return self.proc(arg, reporter)

    def handle_failure(self, error: Exception, arg, reporter: Optional[Reporter]) -> Feedback:
        """Reports the failure according to the node severity"""
        severity = self.severity
        if reporter and (severity is Severity.NORMAL):
            reporter(self.name).report(error, input=arg)
        elif severity is Severity.REQUIRED:
            reporter = (reporter or Reporter)(self.name)
            raise FailureException(reporter.failure(error, input=arg), reporter)
        return False, None


class AsyncNode(Node):
    fun: SingleInputAsyncFunction
    is_async = True

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        try:
            return True, await self.fun(arg)
        except Exception as error:
            return self.handle_failure(error, arg, reporter)

    def proc(self, arg, reporter: Optional[Reporter]) -> Feedback:
        return asyncio.run(self.aproc(arg, reporter))


class PassiveNode(BaseNode):
    """A node that returns the input as it is"""
    is_async = False

    def proc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        return True, arg

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        return True, arg

    def rn(self, name: str) -> 'PassiveNode':
        return self


class WrapperNode(BaseNode, ABC):
    __slots__ = ('node',)

    def __init__(self, node: BaseNode, /, *, severity: Severity = Severity.NORMAL) -> None:
        super().__init__(severity=severity)
        self.node: BaseNode = node

    @property
    def severity(self) -> Severity:
        return self.node.severity

    @severity.setter
    def severity(self, severity: Severity) -> None:
        self.node.severity = severity

    @property
    def is_async(self) -> bool:
        return self.node.is_async


class SemanticNode(WrapperNode):
    """This node holds the label for to be reported in case of failure"""
    __slots__ = ('__name',)
    __name: str

    def __init__(self, node: BaseNode, /, name: str, *, severity: Severity = Severity.NORMAL) -> None:
        super().__init__(node, severity=severity)
        self.name = name

    def proc(self, arg, reporter: Optional[Reporter]) -> Feedback:
        return self.node.proc(arg, (reporter or Reporter)(self.name))

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        return await self.node.aproc(arg, (reporter or Reporter)(self.name))

    @property
    def name(self) -> str:
        """Gets the label of the node (Read-only)"""
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        validate_name(name)
        self.__name = name

    def rn(self, name: str) -> Self:
        return self.__class__(self.node, name, severity=self.severity)


class Loop(WrapperNode):
    """Wrapper node that processes each element of the input through the wrapped node and returns a list of results"""

    def proc(self, args: Iterable, /, reporter: Optional[Reporter]) -> Feedback:
        try:
            iter(args)
        except TypeError:
            return self.node.proc(args, reporter)
        if not args:
            return True, []
        successes: set[bool] = set()
        results = []
        node = self.node
        for arg in args:
            success, res = node.proc(arg, reporter)
            successes.add(success)
            results.append(res)
        return (True in successes), results

    async def aproc(self, args: Iterable, /, reporter: Optional[Reporter]) -> Feedback:
        try:
            iter(args)
        except TypeError:
            return await self.node.aproc(args, reporter)
        if not args:
            return True, []
        node = self.node
        jobs = await asyncio.gather(*(asyncio.create_task(node.aproc(arg, reporter)) for arg in args))
        successes, results = zip(*jobs)
        return (True in successes), list(results)


class NodeGroup(BaseNode, ABC):
    __slots__ = ('_nodes', '__is_async')
    _nodes: tuple[BaseNode, ...]
    __is_async: bool

    def __init__(self, nodes: Iterable[BaseNode], /, *, severity: Severity = Severity.NORMAL) -> None:
        super().__init__(severity=severity)
        self._nodes = tuple(nodes)
        self.__is_async = any(node.is_async for node in self._nodes)

    @property
    def is_async(self) -> bool:
        return self.__is_async

    @property
    def severity(self) -> Severity:
        return self._severity

    @severity.setter
    def severity(self, severity: Severity) -> None:
        self._severity = severity
        if severity is not Severity.REQUIRED:
            return
        _nodes = []
        for node in self._nodes:
            if node.severity is not Severity.NORMAL:
                _nodes.append(node)
                continue
            node = copy(node)
            node.severity = Severity.REQUIRED
            _nodes.append(node)
        self._nodes = tuple(_nodes)


class NodeChain(NodeGroup):
    def proc(self, arg, reporter: Optional[Reporter]) -> Feedback:
        for node in self._nodes:
            success, res = node.proc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        for node in self._nodes:
            success, res = await node.aproc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
                return False, None
            arg = res
        return True, arg

    def __or__(self, other):
        if self.severity is not Severity.NORMAL:
            return chain(self, other)
        return chain(*self._nodes, other)

    def __ior__(self, other):
        if self.severity is not Severity.NORMAL:
            return chain(other, self)
        return chain(other, *self._nodes)

    def __mul__(self, other):
        if self.severity is not Severity.NORMAL:
            return chain(self, loop(other))
        return chain(*self._nodes, loop(other))

    def __imul__(self, other):
        if self.severity is not Severity.NORMAL:
            return chain(loop(other), self)
        return chain(loop(other), *self._nodes)


class NodeList(NodeGroup):
    """A node that processes the input through multiple branches and returns a list as a result"""
    def proc(self, arg, reporter: Optional[Reporter]) -> Feedback:
        successes: set[bool] = set()
        results = []
        for node in self._nodes:
            success, result = node.proc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
            successes.add(success)
            results.append(result)
        if True in successes:
            return True, results
        return False, None

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        successes: set[bool] = set()
        results = []
        for (success, result), node in zip(
                await asyncio.gather(
                    *(asyncio.create_task(node.aproc(arg, reporter)) for node in self._nodes)
                ),
                self._nodes,
                # strict=True
        ):
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
            successes.add(success)
            results.append(result)
        if True in successes:
            return True, results
        return False, None


class NodeDict(NodeList):
    """A node that processes the input through multiple branches and returns a dictionary as a result"""
    __slots__ = ('_branches',)
    _branches: tuple[str, ...]

    def __init__(self, nodes: Iterable[BaseNode], branches: Iterable[str], /):
        super().__init__(nodes)
        self._branches = tuple(branches)

    def proc(self, arg, reporter: Optional[Reporter]) -> Feedback:
        successes: set[bool] = set()
        results = {}
        for branch, node in zip(self._branches, self._nodes):
            success, result = node.proc(arg, reporter)
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
            successes.add(success)
            results[branch] = result
        if True in successes:
            return True, results
        return False, None

    async def aproc(self, arg, /, reporter: Optional[Reporter]) -> Feedback:
        successes: set[bool] = set()
        results = {}
        for (success, result), node, branch in zip(
                await asyncio.gather(
                    *(asyncio.create_task(node.aproc(arg, reporter)) for node in self._nodes)
                ),
                self._nodes,
                self._branches,
                # strict=True
        ):
            if not success:
                if node.severity is Severity.OPTIONAL:
                    continue
            successes.add(success)
            results[branch] = result
        if True in successes:
            return True, results
        return False, None


def _caller(node: 'BaseNode', arg, reporter: Optional[Reporter]):
    return node.proc(arg, reporter)[1]


async def _async_caller(node: 'BaseNode', arg, reporter: Optional[Reporter]):
    return (await node.aproc(arg, reporter))[1]


def loop(*nodes, name: str = None) -> BaseNode:
    """Builds a node that applies to each element of the input"""
    node = _build(nodes, name=name)
    if isinstance(node, PassiveNode):
        return node
    return Loop(node)


def optional(*nodes, name: str = None) -> BaseNode:
    """
    Builds an optional node that will be ignored in case of failures.

    This is useful for nodes that are expected to fail for some inputs,
    and shouldn't be reported, but either ignored as if they don't exist.
    """
    return _build(nodes, name=name).optional()


def required(*nodes, name: str = None) -> BaseNode:
    """Builds a node that stops the entire chain in case of failures"""
    return _build(nodes, name=name).required()


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


def chain(*nodes, name: str = None) -> BaseNode:
    """This function is used to compose functions and create callable\
    objects depending on the given structure.

    It takes arbitrary positional arguments that represent the chain nodes, \
    and takes an optional keyword argument **name** to assign a name to the\
    resulting node.

    The nodes can be one of the following types:

    - A function (simple *leaf* node)
    - A tuple of functions or any of the mentioned node types
    - A dictionary of functions or any of the mentioned node types
    - A list of functions or any of the mentioned node types
    - And finally any other type will be considered a static result, \
    which means that the node will return the same object regardless of\
    the input.

    If the name is specified, the node (chain, model or function)
    will be labeled with that name, and will be used in failure
    reports.

    The resulting object will be a callable object that takes a single\
    argument and returns result of the processing.

    That object takes and optional second argument a Reporter object \
    that can be used to report failures.

    However, if the reporter is omitted, the errors will be silently\
    ignored.
    """
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
    return static(obj)


def _build_node(fun: SingleInputFunction, /, name: Optional[str] = None) -> Node:
    """Builds a leaf node from a function"""
    while isinstance(fun, Node):
        # In case of nested nodes (Node(Node(...))
        name = name or fun.name
        fun = fun.fun
    if name is None:
        name = get_function_name(fun)
    else:
        validate_name(name)
    return (AsyncNode if is_async(fun) else Node)(fun, name)


def _build_node_list(struct: list[Any], /, name: Optional[str] = None) -> BaseNode:
    """Builds a branched node dict"""
    _nodes = tuple(map(_build, struct))
    node: BaseNode = NodeList(_nodes)
    if name:
        return node.rn(name)
    return node


def _build_node_dict(struct: dict[str, Any], /, name: Optional[str] = None) -> BaseNode:
    """Builds a branched node list"""
    _branches = []
    _nodes = []
    for key, value in struct.items():
        branch_name = str(key)
        _branches.append(branch_name)
        _nodes.append(_build(value, branch_name))
    node: BaseNode = NodeDict(_nodes, _branches)
    if name:
        return node.rn(name)
    return node


def _build_chain(nodes: tuple, /, name: Optional[str] = None) -> BaseNode:
    """Builds a sequential chain of nodes"""
    if not nodes:
        return PassiveNode()
    if len(nodes) == 1:
        return _build(nodes[0], name)
    _nodes: list[BaseNode] = list(filter(lambda x: not isinstance(x, PassiveNode), map(_build, nodes)))
    node: BaseNode = NodeChain(_nodes)
    if name:
        node = node.rn(name)
    return node


@overload
def _node(fun: SingleInputAsyncFunction, /, name: Optional[str] = ...) -> AsyncNode: ...
@overload
def _node(fun: SingleInputFunction, /, name: Optional[str] = ...) -> Node: ...


def _node(fun: SingleInputFunction, /, name: Optional[str] = None) -> Node:
    if not callable(fun):
        raise TypeError("The node function must be callable")
    return _build_node(fun, name)
