"""
This module contains the chain parser that convert
descriptive structure to a chain tree structure,
it also contains helper functions to customize chain nodes like:
chainable, funfact, match, ...
"""
import typing as tp
from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS
from inspect import signature

import fastchain.chainables as cb
from ._tools import bind
from .chainables import Chainable, Node, Sequence, DictModel, Match, ListModel


def _parse(obj, *, options: list[tp.Callable[[Chainable], Chainable]] | None = None) -> Chainable:
    """helper function to recursively parse chain structures to chain actual nodes"""
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


def _parse_all(objs: tp.Iterable) -> tp.Generator[Chainable, None, None]:
    """helper function that recursively parse an iterable of chain structures to actual chain nodes"""
    for obj in objs:
        yield _parse(obj)


def parse(obj, root: str | None = None) -> Chainable:
    """converts the chainable to a chain node"""
    chainable_object = _parse(obj)
    chainable_object.set_title(root)
    return chainable_object


def sequence(*members) -> Sequence | Chainable:
    """parses a sequence of chainables into a Sequence"""
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
    members_ = list(filter(lambda x: x is not cb.PASS, members_))  # cleaning unnecessary PASS
    if not members_:
        raise ValueError("a sequence must contain at least one node")
    elif len(members_) == 1:
        return members_[0]
    return Sequence(*members_)


def dict_model(**members) -> DictModel:
    """parses a sequence of keyword chainables into a DictModel"""
    members_: dict[str, Chainable] = {str(k): _parse(v) for k, v in members.items()}
    if len(members_) < 1:
        raise ValueError("cannot create a chain-model with less than 1 members")
    return DictModel(**members_)


def list_model(*members) -> ListModel:
    """parses a sequence of chainables into a ListModel"""
    members_: tuple[Chainable, ...] = tuple(_parse_all(members))
    if len(members_) < 1:
        raise ValueError("cannot create a chain-model with less than 1 members")
    return ListModel(*members_)


def match(*members) -> Match:
    """
    define a matching node that passes each item from an iterable (e.g. list)
    to a corresponding branch (same order)

    :param members: a function or any other supported structure that will be a branch
    :return: node that returns a tuple of results
    :rtype: Match
    """
    members_: tuple[Chainable, ...] = tuple(_parse_all(members))
    if len(members_) < 2:
        raise ValueError("cannot create a chain-match with less than 2 members")
    elif any(member.optional for member in members_):
        raise ValueError("chain-match cannot contain optional members")
    return Match(*_parse_all(members))


@tp.overload
def chainable(func: cb.CHAINABLE, /, name: str | None = ..., default: tp.Any = ...) -> Node: ...
@tp.overload
def chainable(func: cb.CHAINABLE, /, name: str | None = ..., default_factory: tp.Callable[[], tp.Any] | None = ...) -> Node: ...  # noqa: E501
@tp.overload
def chainable(func: tp.Callable, /, *args, name: str | None = ..., default: tp.Any = ..., **kwargs) -> Node: ...  # noqa: E501
@tp.overload
def chainable(func: tp.Callable, /, *args, name: str | None = ..., default_factory: tp.Callable[[], tp.Any] | None = ..., **kwargs) -> Node: ...  # noqa: E501


def chainable(func, /, *args, name=None, default=None, default_factory=None, **kwargs):
    """
    prepares a node with custom settings and optionally pass some partial arguments.

    if the function requires more than 1 positional argument, it is mandatory
    to pass the remaining arguments as chains only expect functions with a signature (Any) -> Any

    naming nodes is recommended when using lambda functions to better identify them in reports,
    and giving them a default will replace the result in case of errors.

    :param func: function (or any callable)
    :param args: any positional argument will be partially applied at the beginning to the function
    :param kwargs: any keyword argument (except the reserved) will be partially applied to the function
    :param name: a name for the node, otherwise function.__qualname__ will be the name
    :param default: value to be returned in case of failure, default to None
    :param default_factory: 0-argument function that generates a default value (recommended for mutable default objects)
    :return: new chain node
    :rtype: Node
    """
    if args or kwargs:
        func = partial(func, *args, **kwargs)
    node = Node(func, name=name, default=default)

    if default_factory is None:
        return node
    elif not callable(default_factory):
        raise TypeError("default factory must be a 0-argument callable (function)")
    bind(node, lambda self: default_factory(), 'default_factory')
    return node


ParamSpec = tp.ParamSpec('ParamSpec')


@tp.overload
def funfact(func: tp.Callable[ParamSpec, cb.CHAINABLE], /) -> tp.Callable[ParamSpec, Node]: ...
@tp.overload
def funfact(*, name: str | None = ..., default: tp.Any = ...) -> tp.Callable[[tp.Callable[ParamSpec, cb.CHAINABLE]], tp.Callable[ParamSpec, Node]]: ...  # noqa: E501
@tp.overload
def funfact(*, name: str | None = ..., default_factory: tp.Callable[[], tp.Any] = ...) -> tp.Callable[[tp.Callable[ParamSpec, cb.CHAINABLE]], tp.Callable[ParamSpec, Node]]: ...  # noqa: E501


def funfact(func=None, /, *, name=None, default=None, default_factory=None):
    """
    decorates higher order functions that generates chainable functions ((Any) -> Any)
    to create reusable and customizable chain components,
    the decorator optionally takes parameters similar to chainable function to customize
    the node.

    :param func: a function factory that generates a chainable callable
    :param name: a name for the node, otherwise function.__qualname__ will be the name
    :param default: value to be returned in case of failure, default to None
    :param default_factory: 0-argument function that generates a default value (recommended for mutable default objects)
    :return: function with same spec but returns a ready node instead of chainable function
    """
    def decorator(function: tp.Callable[ParamSpec, cb.CHAINABLE]) -> tp.Callable[ParamSpec, Node]:
        def wrapper(*args: ParamSpec.args, **kwargs: ParamSpec.kwargs):
            return chainable(function(*args, **kwargs), name=name, default=default, default_factory=default_factory)
        if not callable(function):
            raise TypeError(f"funfact takes a callable as first argument not {type(function)}")
        nonlocal name
        if name is None:
            name = Node.get_qualname(function)
        setattr(wrapper, '__signature__', signature(function))
        return update_wrapper(wrapper, function, (*WRAPPER_ASSIGNMENTS, '__defaults__', '__kwdefaults__'))
    return decorator if (func is None) else decorator(func)
