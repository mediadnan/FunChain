from typing import overload, Callable


from .nodes import (
    build, async_build, is_node_async,
    Input, Output, AsyncCallable,
    DictGroupChainable, ListGroupChainable, AsyncDictGroupChainable, AsyncListGroupChainable,
    BaseNode, Node, AsyncNode, Chain, DictGroup, ListGroup,
    AsyncDictGroup, AsyncListGroup, Chainable, Severity,
)


@overload
def nd(*, name: str | None = ...) -> Chain[Input, Input]: ...
@overload
def nd(function: AsyncCallable[Input, Output], *, name: str | None = ...) -> AsyncNode[Input, Output]: ...
@overload
def nd(function: Callable[[Input], Output], *, name: str | None = ...) -> Node[Input, Output]: ...
@overload
def nd(function: AsyncCallable[Input, Output], *, name: str | None = ...) -> AsyncNode[Input, Output]: ...
@overload
def nd(function: Callable[[Input], Output], *, name: str | None = ...) -> Node[Input, Output]: ...
@overload
def nd(structure: AsyncDictGroupChainable[Input], *, name: str | None = ...) -> AsyncDictGroup[Input]: ...
@overload
def nd(structure: AsyncListGroupChainable[Input], *, name: str | None = ...) -> AsyncListGroup[Input]: ...
@overload
def nd(structure: DictGroupChainable[Input], *, name: str | None = ...) -> DictGroup[Input]: ...
@overload
def nd(structure: ListGroupChainable[Input], *, name: str | None = ...) -> ListGroup[Input]: ...


def nd(obj=None, *, name: str | None = None) -> BaseNode:
    """Makes a chainable node from the given object"""
    if obj is None:
        node = Chain([])
    elif is_node_async(obj):
        node = async_build(obj)
    else:
        node = build(obj)
    return node if (name is None) else node.rn(name)


def chain(*nodes: Chainable, name: str = None) -> BaseNode:
    if len(nodes) == 1:
        _node = nodes[0]
    else:
        pass

