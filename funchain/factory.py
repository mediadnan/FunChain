from copy import copy
from typing import Any, Callable, List, Optional, Union, Dict

from ._tools import asyncify, is_async
from .nodes import (
    BaseNode, Node, AsyncNode, Chain, DictGroup, ListGroup,
    AsyncDictGroup, AsyncListGroup, AsyncBaseNode, SemanticNode, AsyncSemanticNode, AsyncChain,
)


Chainable = Union[BaseNode, Callable, List[Any], Dict[str, Any], Ellipsis]


def foreach(node: Chainable) -> BaseNode:
    """Builds a node that applies to each element of the input"""
    raise NotImplementedError


def optional(node: Chainable) -> BaseNode:
    """Builds a node that will be ignored in case of failures"""
    raise NotImplementedError


def required(node: Chainable) -> BaseNode:
    """Builds a node that stops the entire chain in case of failures"""
    raise NotImplementedError


def chain(*nodes: Chainable, name: str = None) -> BaseNode:
    """Builds a chain of nodes"""
    raise NotImplementedError


def _build(obj: Chainable) -> BaseNode:
    if isinstance(obj, BaseNode):
        return copy(obj)
    elif callable(obj):
        return Node(obj)
    elif isinstance(obj, (list, dict)):
        if isinstance(obj, dict):
            return DictGroup([(key, SemanticNode(_build(item), str(key))) for key, item in obj.items()])
        return ListGroup([(index, SemanticNode(_build(item), str(index))) for index, item in enumerate(obj)])
    elif obj is Ellipsis:
        return Chain([])
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")


def _async_build(obj) -> AsyncBaseNode:
    if isinstance(obj, BaseNode):
        return obj.to_async()
    elif callable(obj):
        return AsyncNode(asyncify(obj))
    elif isinstance(obj, (list, dict)):
        if isinstance(obj, dict):
            return AsyncDictGroup([(key, AsyncSemanticNode(_async_build(item), str(key))) for key, item in obj.items()])
        return AsyncListGroup(
            [(index, AsyncSemanticNode(_async_build(item), str(index))) for index, item in enumerate(obj)]
        )
    elif obj is Ellipsis:
        return AsyncChain([])
    raise TypeError(f"Unsupported type {type(obj).__name__} for chaining")
