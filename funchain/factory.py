from functools import wraps
from typing import Any, Callable, ParamSpec, overload, Iterable

from ._tools import validate_name, get_function_name
from ._tools import is_async
from .nodes import (
    BaseNode,
    Node,
    AsyncNode,
    NodeChain,
    NodeDict,
    NodeList,
    SingleInputFunction,
    PassiveNode,
    Loop,
    Severity
)


PS = ParamSpec('PS')
PASS = object()


def foreach(node, /) -> BaseNode:
    """Builds a node that applies to each element of the input"""
    _node = build(node)
    return (AsyncLoop if isinstance(_node, AsyncBaseNode) else Loop)(_node)


def optional(node, /) -> BaseNode:
    """Builds a node that will be ignored in case of failures"""
    _node = build(node)
    _node.severity = Severity.OPTIONAL
    return _node


def required(node, /) -> BaseNode:
    """Builds a node that stops the entire chain in case of failures"""
    _node = build(node)
    _node.severity = Severity.REQUIRED
    return _node


def static(obj, /) -> Node:
    """Builds a node that returns that same object regardless of the input"""
    _name = str(obj)
    if len(_name) > 20:
        # Shorten long names
        _name = _name[: 8] + '...' + _name[len(_name) - 7:]
    return _build_node(lambda _: obj, f'static_node({_name})')


def chain(*nodes, name: str | None = None) -> BaseNode:
    """Composes nodes in a sequential chain"""
    return build(nodes, name)


def build(obj=PASS, /, name: str | None = None) -> BaseNode:
    """Creates a callable object from the given composition"""
    if isinstance(obj, BaseNode):
        return obj if (name is None) else obj.rn(name)
    elif callable(obj):
        return _build_node(obj, name)
    elif isinstance(obj, tuple):
        return _build_chain(obj, name)
    elif isinstance(obj, dict):
        return _build_dict_group(obj, name)
    elif isinstance(obj, list):
        return _build_group(obj, name)
    elif obj is PASS:
        return PassiveNode()
    return static(obj)


def _build_node(fun: SingleInputFunction, /, name: str | None = None) -> Node:
    """Builds a leaf node from a function"""
    if name is None:
        name = get_function_name(fun)
    else:
        validate_name(name)
    return (AsyncNode if is_async(fun) else Node)(fun, name)


def _build_group(struct: list[Any], /, name: str | None = None) -> BaseNode:
    """Builds a branched node dict"""
    _nodes = tuple(map(build, struct))
    node = NodeList(_nodes)
    return _process_node_group(node, _nodes, name)


def _build_dict_group(struct: dict[str, Any], /, name: str | None = None) -> BaseNode:
    """Builds a branched node list"""
    _branches = tuple(map(str, struct.keys()))
    _nodes = tuple(map(build, struct.values()))
    node = NodeDict(_nodes, _branches)
    return _process_node_group(node, _nodes, name)


def _build_chain(nodes: tuple, /, name: str | None = None) -> BaseNode:
    """Builds a sequential chain of nodes"""
    if not nodes:
        return PassiveNode()
    if len(nodes) == 1:
        return build(nodes[0], name)
    _nodes: list[BaseNode] = list(filter(lambda x: not isinstance(x, PassiveNode), map(build, nodes)))
    _node: BaseNode = NodeChain(_nodes)
    return _process_node_group(_node, _nodes, name)


def _process_node_group(node: BaseNode, nodes: Iterable[BaseNode], name: str | None) -> BaseNode:
    """Converts all nodes into async if there's any async node present, \
    and optionally renames the wrapper node if the name is given."""
    if any(isinstance(_node, AsyncBaseNode) for _node in nodes):
        node = node.to_async()
    if name is not None:
        node = node.rn(name)
    return node
