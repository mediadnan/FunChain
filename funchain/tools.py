from typing import overload, Callable


from .nodes import (
    build, async_build, is_node_async,
    Input, Output, AsyncCallable,
    DictGroupChainable, ListGroupChainable, AsyncDictGroupChainable, AsyncListGroupChainable,
    BaseNode, Node, AsyncNode, Chain, DictGroup, ListGroup,
    AsyncDictGroup, AsyncListGroup, Chainable, Severity,
)


@overload
def nd() -> Chain[Input, Input]: ...
@overload
def nd(function: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def nd(function: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def nd(function: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def nd(function: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def nd(structure: AsyncDictGroupChainable[Input]) -> AsyncDictGroup[Input]: ...
@overload
def nd(structure: AsyncListGroupChainable[Input]) -> AsyncListGroup[Input]: ...
@overload
def nd(structure: DictGroupChainable[Input]) -> DictGroup[Input]: ...
@overload
def nd(structure: ListGroupChainable[Input]) -> ListGroup[Input]: ...


def nd(obj=None) -> BaseNode:
    """Makes a chainable node from the given object"""
    if obj is None:
        return Chain()
    if is_node_async(obj):
        return async_build(obj)
    return build(obj)


def optional(node: Chainable) -> BaseNode:
    _node = build(node)
    _node.severity = Severity.OPTIONAL
    return _node


def required(node: Chainable) -> BaseNode:
    _node = build(node)
    _node.severity = Severity.REQUIRED
    return _node
