import typing as tp
from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS
from inspect import signature

from ._tools import get_qualname
import fastchain.chainables as cb
from .chainables import Chainable, ChainableObject, Node, Sequence, DictModel, Match, ListModel

SPEC = tp.ParamSpec('SPEC')
OPTIONS: tp.TypeAlias = tp.Literal['*', '?']
CHAINABLES: tp.TypeAlias = tp.Union[cb.Chainable,
                                    cb.CHAINABLE,
                                    tuple['CHAINABLES', ...],
                                    list['CHAINABLES'],
                                    dict[str, 'CHAINABLES'],
                                    OPTIONS]


def _parse(
        obj: CHAINABLES, *,
        options: list[tp.Callable[[ChainableObject], ChainableObject]] | None = None
) -> ChainableObject:
    co: Chainable
    if isinstance(obj, Chainable):
        co = obj
    elif callable(obj):
        co = Node(obj)
    elif isinstance(obj, tuple):
        co = sequence(*obj)
    elif isinstance(obj, dict):
        co = dict_model(**obj)
    elif isinstance(obj, list):
        co = list_model(*obj)
    elif obj is Ellipsis:
        return cb.PASS
    else:
        raise TypeError(f"unchainable type {type(obj)}.")

    if options:
        for option in options:
            co = option(co)
    return co


def _parse_all(objs: tp.Iterable[CHAINABLES]) -> tp.Generator[Chainable, None, None]:
    for obj in objs:
        yield _parse(obj)


def parse(obj: CHAINABLES, root: str | None = None) -> Chainable:
    chainable_object = _parse(obj)
    chainable_object.set_title(root)
    return chainable_object


def sequence(*members: CHAINABLES) -> Sequence | Chainable:
    options_ = list()
    members_: list[Chainable] = list()
    for member in members:
        if isinstance(member, str):
            try:
                option_ = cb.OptionMap[member]
            except KeyError:
                raise ValueError(f'unknown chain option {member!r}')
            else:
                options_.append(option_)
        else:
            members_.append(_parse(member, options=options_))
            options_ = list()
    if not members_:
        raise ValueError("cannot create an empty sequence, you can pass '...' instead.")
    elif len(members_) == 1:
        return members_[0]
    return Sequence(*filter(lambda x: x is not cb.PASS, members_))  # cleaning unnecessary PASS


def dict_model(**members: CHAINABLES) -> DictModel:
    members_: dict[str, Chainable] = {str(k): _parse(v) for k, v in members.items()}
    if len(members_) < 1:
        raise ValueError("cannot create a chain-model with less than 1 members")
    return DictModel(**members_)


def list_model(*members: CHAINABLES) -> ListModel:
    members_: tuple[Chainable] = tuple(_parse_all(members))
    if len(members_) < 1:
        raise ValueError("cannot create a chain-model with less than 1 members")
    return ListModel(*members_)


def match(*members: CHAINABLES) -> Match:
    members_: tuple[Chainable] = tuple(_parse_all(members))
    if len(members_) < 2:
        raise ValueError("cannot create a chain-match with less than 2 members")
    return Match(*_parse_all(members))


@tp.overload
def funfact(func: tp.Callable[SPEC, cb.CHAINABLE], /) -> tp.Callable[SPEC, Node]: ...
@tp.overload
def funfact(*, name: str | None = ..., default: tp.Any = ...) -> tp.Callable[[tp.Callable[SPEC, cb.CHAINABLE]], tp.Callable[SPEC, Node]]: ...                        # noqa: E501
@tp.overload
def funfact(*, name: str | None = ..., default_factory: tp.Callable[[], tp.Any] = ...) -> tp.Callable[[tp.Callable[SPEC, cb.CHAINABLE]], tp.Callable[SPEC, Node]]: ...  # noqa: E501


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
            return Node(
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
def chainable(func: cb.CHAINABLE, /, name: str | None = ..., default: tp.Any = ..., default_factory: tp.Callable[[], tp.Any] | None = ...) -> Node: ...                  # noqa: E501
@tp.overload
def chainable(func: tp.Callable, /, *args, name: str | None = ..., default: tp.Any = ..., default_factory: tp.Callable[[], tp.Any] | None = ..., **kwargs) -> Node: ...  # noqa: E501


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
    :return: Node object (partially initialized node)
    """
    if args or kwargs:
        func = partial(func, *args, **kwargs)
    return Node(func, name=name, default=default, default_factory=default_factory)
