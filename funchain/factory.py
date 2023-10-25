from functools import wraps
from typing import Any, Callable, Union, ParamSpec, overload

from ._tools import validate_name, get_function_name
from ._tools import is_async
from .nodes import (
    BaseNode,
    Node,
    AsyncNode,
    Chain,
    DictGroup,
    ListGroup,
    AsyncBaseNode,
    SingleInputFunction,
    PassiveNode,
    Loop,
    AsyncLoop,
    Severity
)


PS = ParamSpec('PS')
Chainable = Union[BaseNode, Callable, list[Any], dict[str, Any], Ellipsis]


def foreach(node: Chainable, /) -> BaseNode:
    """Builds a node that applies to each element of the input"""
    _node = build(node)
    return (AsyncLoop if isinstance(_node, AsyncBaseNode) else Loop)(_node)


def optional(node: Chainable, /) -> BaseNode:
    """Builds a node that will be ignored in case of failures"""
    _node = build(node)
    _node.severity = Severity.OPTIONAL
    return _node


def required(node: Chainable, /) -> BaseNode:
    """Builds a node that stops the entire chain in case of failures"""
    _node = build(node)
    _node.severity = Severity.REQUIRED
    return _node


def static(obj: Any, /) -> Node:
    """Builds a node that returns that same object regardless of the input"""
    _name = str(obj)
    if len(_name) > 20:
        # Shorten long names
        _name = _name[: 8] + '...' + _name[len(_name) - 7:]
    return _build_node(lambda _: obj, f'static_node({_name})')


def chain(*nodes: Chainable, name: str | None = None) -> BaseNode:
    """Composes nodes in a sequential chain"""
    return build(nodes, name)


def build(obj: Chainable, /, name: str | None = None) -> BaseNode:
    """Creates a callable object from the given composition"""
    if isinstance(obj, BaseNode):
        return obj if name is None else obj.rn(name)
    elif callable(obj):
        return _build_node(obj, name)
    elif isinstance(obj, tuple):
        return _build_chain(obj, name)
    elif isinstance(obj, (list, dict)):
        return _build_group(obj, name)
    elif obj is Ellipsis:
        return PassiveNode()
    return static(obj)


def _build_node(fun: SingleInputFunction, /, name: str | None = None) -> Node:
    """Builds a leaf node from a function"""
    if name is None:
        name = get_function_name(fun)
    else:
        validate_name(name)
    return (AsyncNode if is_async(fun) else Node)(fun, name)


@overload
def component(fun: Callable[PS, SingleInputFunction] | None, /) -> Callable[PS, Node]: ...
@overload
def component(*, name: str | None = ...) -> Callable[[Callable[PS, SingleInputFunction]], Callable[PS, Node]]: ...


def component(fun: Callable[PS, SingleInputFunction] = None, /, *, name: str = None):
    """Decorates function generators to make them produce nodes instead of functions"""
    def decorator(function: Callable[PS, SingleInputFunction], /) -> Callable[PS, Node]:
        @wraps(fun)
        def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> Node:
            return _build_node(function(*args, **kwargs), name)
        if not callable(function):
            raise TypeError("The @facto decorator expects a function as argument")
        nonlocal name
        if name is None:
            name = get_function_name(function)
        return wrapper
    if fun is None:
        return decorator
    return decorator(fun)


def _build_group(struct: dict[str, Chainable] | list[Chainable], /, name: str | None = None) -> BaseNode:
    """Builds a branched node group from the structure"""
    is_dict = isinstance(struct, dict)
    any_async: set[bool] = set()
    branches: list[tuple[str, BaseNode]] = []
    for key, branch in (struct.items() if is_dict else enumerate(struct)):
        _branch = build(branch)
        any_async.add(isinstance(_branch, AsyncBaseNode))
        branches.append((str(key), _branch))
    _node = (DictGroup if is_dict else ListGroup)(branches)
    if any(any_async):
        _node = _node.to_async()
    if name is not None:
        _node = _node.rn(name)
    return _node


def _build_chain(nodes: tuple[Chainable, ...], /, name: str | None = None) -> BaseNode:
    """Builds a sequential chain of nodes or returns"""
    if not nodes:
        return PassiveNode()
    if len(nodes) == 1:
        return build(nodes[0], name)
    any_async: set[bool] = set()
    _nodes: list[BaseNode] = []
    for nd in nodes:
        _node = build(nd)
        if isinstance(_node, PassiveNode):
            continue
        any_async.add(isinstance(_node, AsyncBaseNode))
        _nodes.append(_node)
    _node = Chain(_nodes)
    if any(any_async):
        _node = _node.to_async()
    if name is not None:
        _node = _node.rn(name)
    return _node
