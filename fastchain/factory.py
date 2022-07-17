import abc
import functools
import inspect
from typing import Any, Callable, overload, Generic, ParamSpec

from ._tools import get_qualname
from .chainable import CHAINABLE, Chainable, ChainNode, T2, T1


class PreChainable(abc.ABC):
    """
    PreChainables are reusable objects that hold settings for making
    a custom Chainable object when called with the make method.
    """
    @abc.abstractmethod
    def make(self, root: str, pos: tuple[str | int, ...], **kwargs) -> Chainable:
        """takes parsing arguments and merges them with the preset ones to produce a chainable"""


class PreNode(PreChainable, Generic[T1, T2]):
    """
    PreNode objects are reusable objects holding custom settings for making
    ChainNode objects.
    """

    __slots__ = '__func', '__kwargs', '__df'

    def __init__(
            self,
            function: CHAINABLE[T1, T2],
            *,
            name: str | None = None,
            default: T2 | None = None,
            default_factory: Callable[[], T2 | None] | None = None,
            optional: bool = False,
            mode: str | None = None,
    ):
        if not callable(function):
            raise TypeError(f"function should be callable not {type(function).__name__}")
        self.__func: CHAINABLE = function
        self.__df: Callable[[], Any] = default_factory if callable(default_factory) else lambda: default
        self.__kwargs: dict[str, Any] = dict(
            optional=optional,
            mode=mode,
            name=name
        )

    def make(self, root: str, pos: tuple[str | int, ...], **kwargs) -> ChainNode[T1, T2]:
        """
        called from parser function to product a pre-configured ChainNode instance

        :param root: the name of the chain that owns this node.
        :param pos: the position of this node between the other nodes.
        :key name: the name to be given to the node.
        :key default: the value to be returned when failing.
        :key optional: specifies whether the chain can ignore its failing.
        :key mode: specifies the calling mode.

        :return: ChainNode instance with preset and given settings.
        """
        kwargs.update(root=root, pos=pos)
        kwargs = self.__kwargs | kwargs
        if 'default' not in kwargs:
            kwargs.update(default=self.__df())
        return ChainNode[T1, T2](self.__func, **kwargs)

    @property
    def func(self) -> CHAINABLE[T1, T2]:
        """returns the wrapped function"""
        return self.__func

    def __call__(self, arg: T1) -> T2:
        return self.__func(arg)


def chainable(
        function: CHAINABLE[T1, T2],
        /,
        *,
        name: str | None = None,
        default: Any = None,
        default_factory: Callable[[], Any] | None = None,
        optional: bool = False,
        mode: str | None = None,
        **kwargs,
) -> PreNode[T1, T2]:
    """
    wrapper that presets a chain's node (function) by configuring
    its state *(name, default)* and behaviour *(optional, mode)*.

    :param function: the chainable function (Any) -> Any
    :param name: the name given to the generated component, default to function.__qualname__.
    :param default: the value to be returned when failing, default to None.
    :param default_factory: the function that generates a default value when called, default to None.
    :param optional: specifies whether the chain can ignore its failing, default to False.
    :param mode: specifies the calling mode, default to None.
    :keyword kwargs: any keyword argument to be partially passed to function.
    :return: PreNode object or a decorator that returns a PreNode object.
    """

    return functools.wraps(function)(
        PreNode(
            function,
            name=name,
            default=default,
            default_factory=default_factory,
            optional=optional,
            mode=mode
        )
    )


P = ParamSpec("P")


@overload
def funfact(
        *,
        name: str | None = ...,
        default: Any = ...,
        default_factory: Callable[[], Any] | None = ...,
        optional: bool | None = ...,
        mode: str | None = ...
) -> Callable[[Callable[P, CHAINABLE]], Callable[P, PreNode]]: ...


@overload
def funfact(function: Callable[P, CHAINABLE], /) -> Callable[P, PreNode]: ...


def funfact(
        function: Callable[P, CHAINABLE] | None = None,
        /,
        *,
        name: str | None = None,
        default: Any = None,
        default_factory: Callable[[], Any] | None = None,
        optional: bool | None = None,
        mode: str | None = None
):
    """
    generates a decorator with the given parameters.

    :param function: placeholder in case the decorator is called without parameters over the fun-factory.
    :param name: the name given to the generated component, default to decorated function's __qualname__.
    :param default: the value to be returned when failing, default to None.
    :param default_factory: the function that generates a default value when called, default to None.
    :param optional: specifies whether the chain can ignore its failing, default to None.
    :param mode: specifies the calling mode, default to None.
    """
    def decorator(func: Callable[P, CHAINABLE]) -> Callable[[*P.args, *P.kwargs, ...], CHAINABLE]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs: P) -> PreNode:
            return PreNode(
                func(*args, **{k: v for k, v in kwargs.items() if k not in special_kwargs}),
                name=kwargs.get('name', name),
                default=kwargs.get('default', default),
                default_factory=kwargs.get('default_factory', default_factory),
                optional=kwargs.get('optional', optional),
                mode=kwargs.get('mode', mode)
            )
        nonlocal name
        if name is None:
            name = get_qualname(func)
        special_kwargs = {'name', 'default', 'default_factory', 'optional', 'mode'}.difference(
            set(n for n, p in inspect.signature(func).parameters.items() if p.kind > 0)
        )
        return wrapper
    return decorator if function is None else decorator(function)

