from typing import overload, Callable


from .nodes import (
    build, async_build, is_node_async,
    Input, Output, AsyncCallable,
    DictGroupChainable, ListGroupChainable, AsyncDictGroupChainable, AsyncListGroupChainable,
    BaseNode, Node, AsyncNode, Chain, DictGroup, ListGroup,
    AsyncDictGroup, AsyncListGroup,
)


@overload
def node() -> Chain[Input, Input]: ...
@overload
def node(function: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def node(function: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def node(function: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def node(function: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def node(structure: AsyncDictGroupChainable[Input]) -> AsyncDictGroup[Input]: ...
@overload
def node(structure: AsyncListGroupChainable[Input]) -> AsyncListGroup[Input]: ...
@overload
def node(structure: DictGroupChainable[Input]) -> DictGroup[Input]: ...
@overload
def node(structure: ListGroupChainable[Input]) -> ListGroup[Input]: ...


def node(obj=None) -> BaseNode:
    """Makes a chainable node from the given object"""
    if obj is None:
        return Chain()
    if is_node_async(obj):
        return async_build(obj)
    return build(obj)
