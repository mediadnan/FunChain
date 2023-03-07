import inspect
import functools
from typing import Iterable, overload, Callable, ParamSpec, Any, Literal, TypeAlias

from .reporter import OPTIONAL, REQUIRED
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
    PassiveNode,
    AsyncCallable,
)


Chainable: TypeAlias = ('BaseNode[Input, Output]' |
                        Callable[[Input], Output] |
                        dict[Any, 'Chainable[Input, Output]'] |
                        list['Chainable[Input, Output]'] |
                        tuple['Chainable', ...])


AsyncChainable: TypeAlias = ('AsyncBaseNode[Input, Output]' |
                             AsyncCallable[Input, Output] |
                             Callable[[Input], Output] |
                             dict[Any, 'AsyncChainable[Input, Output]'] |
                             list['AsyncChainable[Input, Output]'] |
                             tuple['AsyncChainable', ...])


def _build(obj: Chainable | AsyncChainable, /) -> BaseNode | AsyncBaseNode:
    """Builds a specific node based on the given type"""
    if isinstance(obj, BaseNode):
        return obj.copy()
    elif callable(obj):
        return node(obj, name=None)
    elif isinstance(obj, tuple):
        return chain(*obj, name=None)
    elif isinstance(obj, (dict, list)):
        return model(obj, name=None)
    raise TypeError("Unsupported type for chaining")


def _build_nodes(
        items: Iterable[Chainable], /
) -> tuple[Literal[False], list[BaseNode]] | tuple[Literal[True], list[AsyncBaseNode]]:
    """
    Builds a list of nodes based on the given items and
    returns a boolean indicator whether nodes are asynchronous
    """
    nodes = [_build(item) for item in items]
    nodes_are_async = set(isinstance(nd, AsyncNode) for nd in nodes)
    if any(nodes_are_async):
        if not all(nodes_are_async):
            nodes = [nd.to_async() for nd in nodes]
        return True, nodes
    return False, nodes


GUESS_NAME = object()


@overload
def node() -> PassiveNode[Input]: ...
@overload
def node(func: AsyncCallable[Input, Output], /, *, name: str | None = ...) -> AsyncNode[Input, Output]: ...
@overload
def node(func: Callable[[Input], Output], /, *, name: str | None = ...) -> Node[Input, Output]: ...


def node(
        func: Callable[[Input], Output] | None = None, /, *,
        name: Any = GUESS_NAME
) -> PassiveNode[Input] | Node[Input, Output] | AsyncNode[Input, Output]:
    if func is None:
        return PassiveNode(None)
    elif not callable(func):
        raise TypeError("node function must be callable")
    if name is None:
        name = get_name(func)
    node_ = AsyncNode(func) if is_async(func) else Node(func)
    node_.name = get_name(func) if (name is None) else name
    return node_


def chain(*args: Chainable, name: str | Any = GUESS_NAME) -> BaseNode | AsyncBaseNode:
    are_async, nodes = _build_nodes(args)
    nodes = list(filter(None, nodes))
    if not nodes:
        return PassiveNode(None)
    elif len(nodes) == 1:
        return nodes[0]
    nd = AsyncChain(nodes) if are_async else Chain(nodes)
    nd.name = get_varname() if name is GUESS_NAME else name
    return nd


def loop(*args: Chainable, name: str | Any = GUESS_NAME) -> Loop | AsyncLoop:
    nd = AsyncLoop(nd) if isinstance((nd := chain(*args)), AsyncBaseNode) else Loop(nd)
    nd.name = get_varname() if name is GUESS_NAME else name
    return nd


def model(
        struct: list[Chainable] | dict[Any, Chainable], /, *,
        name: str | None = None
) -> ListModel | DictModel | AsyncListModel | AsyncDictModel:
    if isinstance(struct, dict):
        branches, items = zip(*struct.items())
        models = DictModel, AsyncDictModel
    elif isinstance(struct, list):
        branches, items = zip(*enumerate(struct))
        models = ListModel, AsyncListModel
    else:
        raise TypeError(f"model must be either an instance of {list} or {dict}")
    are_async, nodes = _build_nodes(items)
    nd = models[are_async](list(zip(branches, nodes, strict=True)))
    nd.name = name
    return nd


SPEC = ParamSpec('SPEC')


def node_maker(function: Callable[SPEC, Chainable[Input, Output]], /) -> Callable[SPEC, Node[Input, Output]]:
    """
    node_maker decorator is a shorthand used over (higher order functions)
    that produce some function based on a specific configuration,

    this decorator will make it return the inner function wrapped inside a Node object,
    while keeping the main, so this :

    >>> @node_maker
    ... def my_func(*args, **kwargs):
    ...     def _func(arg):
    ...         pass  # make use of args, kwargs
    ...     return _func

    is equivalent to :

    >>> def my_func(*args, **kwargs):
    ...     def _func(arg):
    ...         pass  # make use of args, kwargs
    ...     return node(_func, name='my_func')

    :param function: a function that returns an inner function (HOF)
    :return: function that returns a Node wrapping the original function
    """
    @functools.wraps(function, (*functools.WRAPPER_ASSIGNMENTS, '__defaults__', '__kwdefaults__'))
    def wrapper(*args: SPEC.args, **kwargs: SPEC.kwargs) -> Node:
        return node(function(*args, **kwargs), name=name)
    if not callable(function):
        raise TypeError(f"node_factory decorator expects a function not {type(function).__qualname__!r}")
    name = get_name(function)
    setattr(wrapper, '__signature__', inspect.signature(function))
    return wrapper


# options
def optional(*items: Chainable | AsyncChainable) -> BaseNode | AsyncBaseNode:
    """makes the node optional"""
    nd = _build(items)
    nd.severity = OPTIONAL
    return nd


def required(*items: Chainable | AsyncChainable) -> BaseNode | AsyncBaseNode:
    """makes the node required"""
    nd = _build(items)
    nd.severity = REQUIRED
    return nd
