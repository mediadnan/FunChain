import abc
import typing as tp
from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS
from inspect import signature

from ._tools import get_qualname
import fastchain.chainables as cb


SPEC = tp.ParamSpec('SPEC')

OPTIONS: tp.TypeAlias = tp.Literal['*', '?', ':']
CHAINABLES: tp.TypeAlias = tp.Union[
    cb.CHAINABLE,
    tuple['CHAINABLES', ...],
    list['CHAINABLES'],
    dict[str, 'CHAINABLES'],
    'Factory',
    OPTIONS
]


class Factory(abc.ABC):
    name: str
    @abc.abstractmethod
    def __call__(self, title: str, **kwargs) -> cb.Chainable: ...


class NodeFactory(Factory):
    def __init__(
            self,
            func: cb.Chainable,
            *,
            name: str | None = None,
            default: tp.Any = None,
            default_factory: tp.Callable[[], tp.Any] | None = None
    ) -> None:
        if not callable(func):
            raise TypeError(f"nodes must be chainable functions (Any) -> Any, not {type(func)}")

        if name is None:
            name = get_qualname(func)
        elif not isinstance(name, str):
            raise TypeError(f"node's name must be a {str} not {type(name)}")
        elif not name:
            raise ValueError("empty strings are not valid node names")

        if default_factory is None:
            def df(): return default
            default_factory = df
        elif not callable(default_factory):
            raise TypeError("default_factory must be a 0-argument function that returns any value")

        self.name: str = name
        self.func: cb.CHAINABLE = func
        self.default_factory: tp.Callable[[], tp.Any] = default_factory

    def __call__(self, title: str, **kwargs) -> cb.Node:
        return cb.Node(self.func, title=title, default_factory=self.default_factory, **kwargs)


class CollectionFactory(Factory):
    transfer_only: set[str] = {}  # values to be passed recursively to members

    @tp.overload
    def __init__(self, constructor: tp.Type[cb.Model], members: tp.Callable[..., dict[str, cb.Chainable]], name: str | None = ...): ...  # noqa
    @tp.overload
    def __init__(self, constructor: tp.Type[cb.Sequence] | tp.Type[cb.Group] | tp.Type[cb.Match], members: tp.Callable[..., list[cb.Chainable]], name: str | None = ...): ...  # noqa: E501

    def __init__(self, constructor, members, name=None):
        if name is None:
            name = constructor.__name__.lower()
        self.name: str = name
        self.constructor = constructor
        self.parse_members = members

    def __call__(self, title, **kwargs):
        members = self.parse_members(title, **{k: v for k, v in kwargs.items() if k in self.transfer_only})
        if not members:
            raise ValueError(f"cannot create an empty {self.name}")
        return self.constructor(members, title=title, **kwargs)


@tp.overload
def funfact(func: tp.Callable[SPEC, cb.CHAINABLE], /) -> tp.Callable[SPEC, NodeFactory]: ...
@tp.overload
def funfact(*, name: str | None = ..., default: tp.Any = ...) -> tp.Callable[[tp.Callable[SPEC, cb.CHAINABLE]], tp.Callable[SPEC, NodeFactory]]: ...                        # noqa: E501
@tp.overload
def funfact(*, name: str | None = ..., default_factory: tp.Callable[[], tp.Any] = ...) -> tp.Callable[[tp.Callable[SPEC, cb.CHAINABLE]], tp.Callable[SPEC, NodeFactory]]: ...  # noqa: E501


def funfact(func=None, /, *, name=None, default=None, default_factory=None):
    """
    decorator that transforms a higher order function that produces a chainable function to
    a similar function that produces a node factory object with the given name and default.

    This decorator can be used without parameters like this:

    >>> @funfact        # default name will be 'factory'
    ... def factory(*args, **kwargs):
    ...     # source omitted ...
    ...     return lambda x: x * 2  # returns chainable function

    Or with a parameters to customize the chainable
    >>> @funfact(name='my_fact')
    ... def factory(*args, **kwargs):
    ...     # source omitted ...
    ...     return lambda x: x * 2


    :param func: higher order function that produces a chainable function (1-argument function).
    :param name: custom name for the node, otherwise function.__qualname__ will be the name.
    :param default: a value that will be returned in case of failure (exception), default to None.
    :param default_factory: 0-argument function that returns a default value (for mutable default objects).
    :return: function with same arg-spec as function but returns a NodeFactory object (partially initialized node).
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            return NodeFactory(
                function(*args, **kwargs),
                name=name,
                default=default,
                default_factory=default_factory,
            )
        if not callable(function):
            raise TypeError(f"funfact decorator expects a function not {type(function)}")
        nonlocal name
        if name is None:
            name = get_qualname(function)
        setattr(wrapper, '__signature__', signature(function))
        return update_wrapper(wrapper, function, (*WRAPPER_ASSIGNMENTS, '__defaults__', '__kwdefaults__'))
    return decorator if func is None else decorator(func)


@tp.overload
def chainable(func: cb.CHAINABLE, /, name: str | None = ..., default: tp.Any = ..., default_factory: tp.Callable[[], tp.Any] | None = ...) -> NodeFactory: ...                  # noqa: E501
@tp.overload
def chainable(func: tp.Callable, /, *args, name: str | None = ..., default: tp.Any = ..., default_factory: tp.Callable[[], tp.Any] | None = ..., **kwargs) -> NodeFactory: ...  # noqa: E501


def chainable(func, /, *args, name=None, default=None, default_factory=None, **kwargs):
    """
    prepares a chain-node factory with the given name and default/default_factory from
    a chainable function, or from a non-chainable if given remaining *args and **kwargs that will
    be partially applied to this function.

    This:

    >>> def half(a):    # chainable function (1-argument)
    ...     return a / 2
    >>>  chainable(half)

    is equivalent to:

    >>> def divide(a, b):   # non_chainable function
    ...     return a / b
    >>> chainable(divide, b=2, name="half")

    or even this:

    >>> chainable(lambda x: divide(x, 2), name="half")

    :param func: function, method, type or any callable object.
    :param args: if provided, they will be partially applied (first) to function.
    :param name: custom name for the node, otherwise function.__qualname__ will be the name.
    :param default: a value that will be returned in case of failure (exception), default to None.
    :param default_factory: 0-argument function that returns a default value (for mutable default objects).
    :param kwargs: if provided, they will be partially applied to function.
    :return: NodeFactory object (partially initialized node)
    """
    if args or kwargs:
        func = partial(func, *args, **kwargs)
    return NodeFactory(func, name=name, default=default, default_factory=default_factory)
