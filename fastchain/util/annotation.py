import types
import typing
import inspect
import functools


_DEFAULTS = {str, bytes, bytearray, dict, set, frozenset, int, float, complex, list, tuple}
_TYPING_ALIASES = {
    typing.ByteString: bytes,
    typing.Dict: dict,
    typing.Set: set,
    typing.FrozenSet: frozenset,
    typing.List: list,
    typing.Tuple: tuple
}
_UnionGenericAlias = type(typing.Union[str, int, None])
_SpecialGenericAlias = type(typing.List)
_GenericAlias = type(typing.List[typing.Any])
_NotSpecified = {
    typing.Any,
    inspect.signature(lambda: None).return_annotation,
    None
}


def _default_default_value() -> None: return


def guess_default(obj) -> typing.Callable[[], typing.Any]:
    """Guesses the default value for a function"""
    if obj in _DEFAULTS:                                            # If builtin types
        return obj
    elif obj in _TYPING_ALIASES:                                    # If 'typing' types
        return _TYPING_ALIASES[obj]
    elif obj in _NotSpecified:                                  # If not specified
        return _default_default_value
    elif isinstance(obj, (types.GenericAlias, _GenericAlias)):      # If type generics like list[str] / List[str]
        origin, args = obj.__origin__, obj.__args__
        if origin in _TYPING_ALIASES:   # map 'typing' type to corresponding builtin type
            origin = _TYPING_ALIASES[origin]  # type: ignore
        if origin is tuple:
            defaults = list(map(guess_default, args))
            return lambda: tuple(default() for default in defaults)
        return guess_default(origin)
    elif callable(obj):                                            # If it's a function, guess from annotation
        return guess_default(inspect.signature(obj).return_annotation)
    return _default_default_value                                   # Otherwise return () -> None


def getname(func: typing.Callable, strip: str = '_') -> str:
    """Gets the functions name"""
    if isinstance(func, functools.partial):
        return getname(func.func)
    try:
        name: str = func.__name__
    except AttributeError:
        name: str = type(func).__name__
    return name.strip(strip)


def is_typed_optional(annotation: typing.Any) -> bool:
    """Checks the annotation and tells whether the node attribute is optional"""
    return any([
        isinstance(annotation, (types.UnionType, _UnionGenericAlias)) and types.NoneType in annotation.__args__,
        annotation is None
    ])
