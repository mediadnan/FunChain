import functools
import warnings
from typing import Coroutine, Iterable, overload, Callable, ParamSpec, Any
from inspect import signature
from functools import update_wrapper, WRAPPER_ASSIGNMENTS

from ._util import get_name, is_async
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
        are_async, nodes = _build_collection(obj)
        nodes = list(filter(None, nodes))
        if len(nodes) == 1:
            return nodes[0]
        return AsyncChain(nodes) if are_async else Chain(nodes)
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
def node(function: Callable[[Input], Coroutine[None, None, Output]], /, name: str = ...) -> AsyncNode: ...
@overload
def node(function: Callable[[Input], Output], /, name: str = ...) -> Node: ...


def node(function: Callable[[Input], Output], /, name: str | None = None) -> Node | AsyncNode:
    if not callable(function):
        raise TypeError("node function must be callable")
    if name is None:
        name = get_name(function)
    node = AsyncNode(function) if is_async(function) else Node(function)
    node.name = get_name(function) if name is None else name
    return node


def chain(*args: Chainable) -> Chain:
    pass


def loop(*args: Chainable) -> Loop | AsyncLoop:
    return AsyncLoop(node) if isinstance((node := chain(*args)), AsyncBaseNode) else Loop(node)


def cb(obj=None, /, name: str | None = None, *args, **kwargs):
    """
    wraps a function (or list / dict of functions) and turns it into a node,
    if called without arguments, the function returns a Node equivalent to
    lambda x: x, and it's more optimized than node(lambda x: x)

    :param obj:
    :type obj:
    :param name:
    :type name:
    :return:
    :rtype:
    """
    if obj is None:
        return PassiveNode()
    if callable(obj):
        if args or kwargs:
            obj = functools.partial(obj, *args, **kwargs)
        return Node(obj, name=name)
    if isinstance(obj, dict):
        return DictModel(obj)
    if isinstance(obj, list):
        return ListModel(obj)
    if isinstance(obj, BaseNode):
        warnings.warn("Passing a Node object to node(...) is useless", stacklevel=2)
        return obj


@overload
def acb() -> AsyncChain[Input]: ...


def acb():
    pass


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
        return cb(function(*args, **kwargs), name=name)
    if not callable(function):
        raise TypeError(f"node_factory decorator expects a function not {type(function).__qualname__!r}")
    name = get_name(function)
    setattr(wrapper, '__signature__', signature(function))
    return update_wrapper(wrapper, function, (*WRAPPER_ASSIGNMENTS, '__defaults__', '__kwdefaults__'))
