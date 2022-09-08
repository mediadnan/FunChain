import abc
from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS, partialmethod
from inspect import signature, ismethod
from typing import Any, Callable, overload, Iterable, Mapping, ParamSpec

from .nodes import (Node,
                    Chainable,
                    Pass,
                    Sequence,
                    DictModel,
                    Match,
                    ListModel)
from .options import OPTIONS, set_default

PASS = Pass()  # fastchain only needs one instance of Pass


class NodeFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(self) -> Node:
        """Returns a brand-new node each time called"""


class match(NodeFactory):  # noqa: used as a function
    __slots__ = '_branches', '_name'

    def __init__(self, *branches, name: str | None = None) -> None:
        if name is None:
            name = 'match'
        elif not isinstance(name, str):
            raise TypeError("The match name must be str")
        self._name: str = name
        self._branches: tuple = branches

    def __call__(self) -> Match:
        return Match([_parse(member) for member in self._branches], self._name)


class chainable(NodeFactory):
    __slots__ = '_function', '_name', '_set_default'

    @overload
    def __init__(self, function: Callable[[Any], Any], /, *, name: str | None = ..., default: Any = ...) -> None: ...
    @overload
    def __init__(self, function: Callable, /, *args, name: str | None = ..., default: Any = ..., **kwargs) -> None: ...
    @overload
    def __init__(self, function: Callable[[Any], Any], /, *, name: str | None = ..., default_factory: Callable[[], Any] = ...) -> None: ...  # noqa
    @overload
    def __init__(self, function: Callable, /, *args, name: str | None = ..., default_factory: Callable[[], Any] = ..., **kwargs) -> None: ...  # noqa

    def __init__(self, function, /, *args, name=None, default=None, default_factory=None, **kwargs):
        if not callable(function):
            raise TypeError("The function must be callable")
        if args or kwargs:
            function = (partialmethod(function, *args, **kwargs)
                        if ismethod(function) else
                        partial(function, *args, **kwargs))
        self._name: str | None = name
        self._function: Callable[[Any], Any] = function
        self._set_default: Callable[[Node], Node] = partial(set_default,
                                                            default=default,
                                                            default_factory=default_factory)

    def __call__(self) -> Chainable:
        return self._set_default(Chainable(self._function, self._name))


def _parse(obj) -> Node:
    if isinstance(obj, NodeFactory):
        return obj()
    elif callable(obj):
        return Chainable(obj)
    elif isinstance(obj, tuple):
        nodes = []
        options = []
        for item in obj:
            if isinstance(item, str):
                if item not in OPTIONS:
                    raise ValueError(f"Unknown options {item!r}")
                options.append(OPTIONS[item])
            else:
                node = _parse(item)
                if node is PASS:
                    options = []
                    continue
                for option in reversed(options):
                    node = option(node)
                nodes.append(node)
        if len(nodes) == 1:
            return nodes[0]
        return Sequence(nodes)
    elif isinstance(obj, list):
        return ListModel(_parse_list(obj))
    elif isinstance(obj, dict):
        return DictModel(_parse_dict(obj))
    elif obj is Ellipsis:
        return PASS
    raise TypeError(f"Unsupported type {type(obj).__name__}")


def _parse_list(objs: Iterable) -> list[Node]:
    """Converts a list of objects into a list of nodes"""
    return [_parse(obj) for obj in objs]


def _parse_dict(objs: Mapping) -> dict[Any, Node]:
    """Converts a dict of objects into a dict of nodes"""
    return {key: _parse(obj) for key, obj in objs.items()}


def parse(obj, root: str | None = None) -> Node:
    node = _parse(obj)
    node.set_title(root)
    return node


Spec = ParamSpec('Spec')


@overload
def funfact(func: Callable[Spec, Callable[[Any], Any]]) -> Callable[Spec, chainable]: ...
@overload
def funfact(name: str | None = ..., default: Any = ...) -> Callable[[Callable[Spec, Callable[[Any], Any]]], Callable[Spec, chainable]]: ...  # noqa
@overload
def funfact(name: str | None = ..., default_factory: Callable[[], Any] | None = ...) -> Callable[[Callable[Spec, Callable[[Any], Any]]], Callable[Spec, chainable]]: ...  # noqa


def funfact(function=None, /, *, name=None, default=None, default_factory=None):
    """
    Decorates higher order functions that produce chainable functions ((Any) -> Any)
    to create reusable and customizable chain components,
    the decorator optionally takes parameters similar to chainable to customize the node.

    :param function: a function factory that generates a chainable callable
    :param name: a name for the node, otherwise function.__qualname__ will be the name
    :param default: value to be returned in case of failure, default to None
    :param default_factory: 0-argument function that generates a default value (recommended for mutable default objects)
    :return: function with same spec but returns a ready node instead of chainable function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return chainable(func(*args, **kwargs), name=name, default=default, default_factory=default_factory)
        if not callable(func):
            raise TypeError("funfact takes a callable as first argument")
        nonlocal name
        if name is None:
            name = Chainable.qualname(func)
        setattr(wrapper, '__signature__', signature(func))
        return update_wrapper(wrapper, func, (*WRAPPER_ASSIGNMENTS, '__defaults__', '__kwdefaults__'))
    return decorator if (function is None) else decorator(function)
