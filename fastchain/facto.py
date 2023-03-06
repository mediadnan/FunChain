import functools
import warnings
from typing import overload, Callable, ParamSpec, Any
from inspect import signature
from functools import update_wrapper, WRAPPER_ASSIGNMENTS

from ._util import get_name, is_async
from .node import (
    BaseNode,
    AsyncBaseNode,
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


def build(obj, /, name: str | None = None) -> BaseNode:
    if isinstance(obj, BaseNode):
        node = obj.copy()
    elif callable(obj):
        name = name or get_name(obj)
        node = AsyncNode(obj) if is_async(obj) else Node(obj)
    elif isinstance(obj, tuple):
        nodes = list(filter(None, (build(item) for item in obj)))
        async_nodes = set(isinstance(node, AsyncNode) for node in nodes)
        if any(async_nodes):
            if not all(async_nodes):
                nodes = [node.to_async() for node in nodes]
            node = AsyncChain(nodes)
        node = Chain(nodes)
    elif isinstance(obj, dict):
        pass
    elif isinstance(obj, list):
        pass
    else:
        raise TypeError("Unsupported type for chaining")




def chain(*args: Chainable) -> Chain:
    pass


@overload
def cb() -> Chain[Input, Input]: ...
@overload
def cb(func: Callable[[Input], Output], /, name: str = ...) -> Node[Input, Output]: ...
@overload
def cb(func: Callable[[Input], Output], /, name: str = ..., *args, **kwargs) -> Node[Input, Output]: ...
@overload
def cb(model: dict[Any, Chainable[Input, Output]], /) -> DictModel[Input, Output]: ...
@overload
def cb(model: list[Chainable[Input, Output]], /) -> ListModel[Input, Output]: ...


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
