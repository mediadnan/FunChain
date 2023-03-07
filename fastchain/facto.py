import functools
import warnings
from typing import Coroutine, Iterable, overload, Callable, ParamSpec, Any
from inspect import signature
from functools import update_wrapper, WRAPPER_ASSIGNMENTS

from ._util import get_name, is_async, get_varname
from .node import (
    AsyncLoop,
    BaseNode,
    AsyncBaseNode,
    Loop,
    Node,
    AsyncNode,
    ListModel,
    AsyncListModel,
    DictModel,
    AsyncDictModel,
    Chain,
    AsyncChain,
    Input,
    Output,
    Chainable,
    PassiveNode,
)


def _build_collection(items: Iterable[Chainable], /) -> tuple[bool, list[BaseNode]]:
    nodes = [build(item) for item in items]
    nodes_are_async = set(isinstance(node, AsyncNode) for node in nodes)
    if any(nodes_are_async):
        if not all(nodes_are_async):
            nodes = [node.to_async() for node in nodes]
        return True, nodes
    return False, nodes


def build(obj, /) -> BaseNode | AsyncBaseNode:
    if isinstance(obj, BaseNode):
        return obj.copy()
    elif callable(obj):
        return node(obj)
    elif isinstance(obj, tuple):
        return chain(*obj)
    elif isinstance(obj, dict):
        branches, items = zip(*obj.items())
        Models = DictModel, AsyncDictModel
    elif isinstance(obj, list):
        branches, items = zip(*enumerate(obj))
        Models = ListModel, AsyncListModel
    else:
        raise TypeError("Unsupported type for chaining")
    are_async, nodes = _build_collection(items)
    return Models[are_async](list(zip(branches, nodes, strict=True)))

@overload
def node() -> PassiveNode: ...
@overload
def node(function: Callable[[Input], Coroutine[None, None, Output]], /, *, name: str = ...) -> AsyncNode[Input, Output]: ...
@overload
def node(function: Callable[[Input], Output], /, *, name: str = ...) -> Node[Input, Output]: ...


def node(function: Callable[[Input], Output], /, *, name: str | None = None) -> Node[Input, Output] | AsyncNode[Input, Output]:
    if not callable(function):
        raise TypeError("node function must be callable")
    if name is None:
        name = get_name(function)
    node_ = AsyncNode(function) if is_async(function) else Node(function)
    node_.name = get_name(function) if name is None else name
    return node_


def chain(*args: Chainable, name: str | None = None) -> Chain | AsyncChain:
    are_async, nodes = _build_collection(args)
    nodes = list(filter(None, nodes))
    if not nodes:
        return PassiveNode()
    elif len(nodes) == 1:
        return nodes[0]
    node_ = AsyncChain(nodes) if are_async else Chain(nodes)
    node_.name = get_varname() if name is None else name
    return node_


def loop(*args: Chainable) -> Loop | AsyncLoop:
    return AsyncLoop(node) if isinstance((node := chain(*args)), AsyncBaseNode) else Loop(node)



SPEC = ParamSpec('SPEC')


def node_factory(function: Callable[SPEC, Chainable[Input, Output]], /) -> Callable[SPEC, Node[Input, Output]]:
    """
    node_factory decorator is a shorthand used over (higher order functions)
    that produce some function based on a specific configuration,

    this decorator will make it return the inner function wrapped inside a Node object,
    while keeping the main, so this :

    >>> @node_factory
    ... def my_func(*args, **kwargs):
    ...     def _func(arg):
    ...         pass  # make use of args, kwargs
    ...     return _func

    is equivalent to :

    >>> def my_func(*args, **kwargs):
    ...     def _func(arg):
    ...         pass  # make use of args, kwargs
    ...     return cb(_func, name='my_func')

    :param function: a function that returns an inner function (HOF)
    :return: function that returns a Node wrapping the original function
    """
    def wrapper(*args: SPEC.args, **kwargs: SPEC.kwargs) -> Node:
        return node(function(*args, **kwargs), name=name)
    if not callable(function):
        raise TypeError(f"node_factory decorator expects a function not {type(function).__qualname__!r}")
    name = get_name(function)
    setattr(wrapper, '__signature__', signature(function))
    return update_wrapper(wrapper, function, (*WRAPPER_ASSIGNMENTS, '__defaults__', '__kwdefaults__'))
