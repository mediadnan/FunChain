import abc
from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS
from inspect import signature
from typing import (
    Any,
    Callable,
    Type,
    Generic,
    TypeAlias,
    Literal,
    Union,
    overload,
    ParamSpec
)
from ._tools import get_qualname
from .chainables import (
    CHAINABLE,
    Chainable,
    Node,
    Pipe,
    Match,
    Group,
    Model,
    PASS,
    CT,
    CCT
)


OPTIONS: TypeAlias = Literal['*', '?', ':']
CHAINABLES: TypeAlias = Union[
    'Factory',
    CHAINABLE,
    tuple[OPTIONS | Any, ...],  # replace 'Any' with 'CHAINABLE' when circular hints get supported.
    list[Any],                  # replace 'Any' with 'CHAINABLE' when circular hints get supported.
    dict[str, Any]              # replace 'Any' with 'CHAINABLE' when circular hints get supported.
]


class Factory(abc.ABC, Generic[CT]):
    name: str
    @abc.abstractmethod
    def __call__(self, title: str, **kwargs) -> CT: ...


class NodeFactory(Factory[Node]):
    name: str

    def __init__(
            self,
            function: CHAINABLE,
            *,
            name: str | None = None,
            default: Any = None,
            default_factory: Callable[[], Any] | None = None,
            **kwargs
    ):
        if not callable(function):
            raise TypeError(f"expected a chainable function but got {type(function)}")
        if name is None:
            name = get_qualname(function)
        if not (default_factory is None or callable(default_factory)):
            raise TypeError("default_factory must be a 0-argument function that returns any value")
        if kwargs:
            function = partial(function, **kwargs)
        self.function = function
        self.name = name
        self.kwargs = dict(default=default, default_factory=default_factory)

    def __call__(self, title: str, **kwargs) -> Node:
        return Node(self.function, title=title, **self.kwargs, **kwargs)


class CollectionFactory(Factory, Generic[CCT]):
    name: str
    constructor: Type[CCT]
    transfer_only: set[str] = {'optional'}  # values to be parsed recursively to members

    @overload
    def __init__(self, cn: Type[Model], members: Callable[..., dict[str, Chainable]]): ...

    @overload
    def __init__(self, cn: Type[Pipe] | Type[Group] | Type[Match], members: Callable[..., list[Chainable]]): ...

    def __init__(self, constructor, members):
        self.name = constructor.__name__.lower()
        self.constructor = constructor
        self.parse_members = members

    def __call__(self, title: str, *_, **kwargs) -> CCT:
        members = self.parse_members(title, **{k: v for k, v in kwargs.items() if k in self.transfer_only})
        if not members:
            raise ValueError(f"cannot create an empty {self.name}")
        return self.constructor(members, title=title, **kwargs)


def parse(
        chainable_object,
        *,
        root: str | None = None,
        branch: Any = None,
        kind: Type[Chainable] | None = None,
        **kwargs
) -> Chainable:

    if root is not None and branch is None:
        root = f'{root}[{branch}]'

    if isinstance(chainable_object, Factory):
        title = chainable_object.name
        if root is not None:
            if branch is not None:
                root = f'{root}[{branch}]'
            title = f'{root}/{title}'
        return chainable_object(title, **kwargs)

    if callable(chainable_object):
        return parse(NodeFactory(chainable_object), root=root, **kwargs)

    elif isinstance(chainable_object, tuple):
        merged: list[tuple[Any, dict[str, Any]]] = []
        options: dict[str, Any] = {}
        for item in chainable_object:
            if isinstance(item, str):
                match item:
                    case '*':
                        options['iterable'] = True
                    case '?':
                        options['optional'] = True
                    case ':':
                        options['kind'] = Match
                    case _:
                        raise ValueError(f"unsupported option {item!r}")
            else:
                merged.append((item, options))
                options = {}
        del options

        if len(merged) == 1:
            return parse(merged[0][0], root=root, branch=branch, **kwargs, **merged[0][1])

        def parse_pipe_members(root_: str | None, **kwargs_) -> list[Chainable]:
            return [parse(obj, root=root_, branch=i, **kwargs_, **ops) for i, (obj, ops) in enumerate(merged)]
        return parse(CollectionFactory[Pipe](Pipe, parse_pipe_members), root=root, branch=branch, **kwargs)

    elif isinstance(chainable_object, dict):
        def parse_model_members(root_: str | None, **kwargs_) -> dict[str, Chainable]:
            return {key: parse(value, root=root_, branch=key, **kwargs_) for key, value in chainable_object.items()}
        return parse(CollectionFactory[Model](Model, parse_model_members), root=root, branch=branch, **kwargs)

    elif isinstance(chainable_object, list):
        def parse_group_members(root_: str | None, **kwargs_) -> list[Chainable]:
            return [parse(obj, root=root_, branch=i, **kwargs_) for i, obj in enumerate(chainable_object)]
        if kind is None or not issubclass(kind, (Group, Match)):
            kind = Group
        return parse(CollectionFactory[Group | Match](kind, parse_group_members), root=root, branch=branch, **kwargs)

    elif chainable_object is Ellipsis:
        return PASS

    else:
        raise TypeError(f"unchainable type {type(chainable_object)}.")


SP = ParamSpec('SP')


@overload
def funfact(func: Callable[SP, CHAINABLE], /) -> Callable[SP, NodeFactory]: ...


@overload
def funfact(
        *,
        name: str | None = ...,
        default: Any = ...,
) -> Callable[[Callable[SP, CHAINABLE]], Callable[SP, NodeFactory]]: ...


@overload
def funfact(
        *,
        name: str | None = ...,
        default_factory: Callable[[], Any] = ...,
) -> Callable[[Callable[SP, CHAINABLE]], Callable[SP, NodeFactory]]: ...


def funfact(
        func: Callable[SP, CHAINABLE] | None = None, /, *,
        name: str | None = None,
        default: Any = None,
        default_factory: Callable[[], Any] | None = None,
) -> Callable[SP, NodeFactory] | Callable[[Callable[SP, CHAINABLE]], Callable[SP, NodeFactory]]:
    """
    decorator that transforms a higher order function that produces a chainable function to
    a similar function that produces a node factory object with the given name and default.


    :param func: higher order function that produces a chainable function (1-argument function).
    :param name: custom name for the node, otherwise func.__qualname__ will be the name.
    :param default: a value that will be returned in case of failure (exception), default to None.
    :param default_factory: 0-argument function that returns a default value (for mutable default objects).
    :return: function with same arg-spec as func but returns a NodeFactory object (partially initialized node).
    """
    def decorator(function: Callable[SP, CHAINABLE]) -> Callable[SP, NodeFactory]:
        def wrapper(*args: SP.args, **kwargs: SP.kwargs) -> NodeFactory:
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


@overload
def chainable(
        func: CHAINABLE, /,
        name: str | None = ...,
        default: Any = ...,
        default_factory: Callable[[], Any] | None = ...
) -> NodeFactory: ...


@overload
def chainable(
        func: Callable, /,
        *args,
        name: str | None = ...,
        default: Any = ...,
        default_factory: Callable[[], Any] | None = ...,
        **kwargs
) -> NodeFactory: ...


def chainable(func: Callable, /, *args, name=None, default=None, default_factory=None, **kwargs) -> NodeFactory:
    """
    prepares a chain node with the given name and default/default_factory from a chainable function
    ( 1-argument function), or from a non-chainable if given remaining *args and **kwargs.

    :param func: function, method, type or any callable object.
    :param args: if provided, they will be partially applied to func.
    :param name: custom name for the node, otherwise func.__qualname__ will be the name.
    :param default: a value that will be returned in case of failure (exception), default to None.
    :param default_factory: 0-argument function that returns a default value (for mutable default objects).
    :param kwargs: if provided, they will be partially applied to func.
    :return: NodeFactory object (partially initialized node)
    """
    if args or kwargs:
        func = partial(func, *args, **kwargs)
    return NodeFactory(func, name=name, default=default, default_factory=default_factory)
