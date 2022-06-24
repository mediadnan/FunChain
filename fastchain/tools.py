from typing import (
    Any,
    Union,
    Tuple,
    TypeVar,
    Callable,
)

_T = TypeVar('_T')


def validate(
        var: _T,
        var_name: str,
        var_type: Union[type, Tuple[type, ...]] = None,
        *conditions: Union[Callable[[Any], bool], bool],
        err_msg: str = None
) -> _T:
    """
    validates the type and optionally the value of a variable and returns it.

    :param var: the variable to be checked
    :param var_name: the variable name to be referenced in exceptions
    :param var_type: the expected type or types
    :param conditions: either a checker function or True for truthy value
    :param err_msg: custom message to be displayed if one of the condition failed

    :returns: the value if everything passes
    """
    if var_type and not isinstance(var, var_type):
        if isinstance(var_type, tuple):
            raise TypeError(f"{var_name!r} must be either {' or '.join(type(t).__name__ for t in var_type)}")
        raise TypeError(f"{var_name!r} must be {type(var_type).__name__}")
    for condition in conditions:
        if callable(condition) and condition(var) or isinstance(condition, bool) and condition == bool(var):
            continue
        raise ValueError(err_msg or f"invalid value {var!r} for {var_name!r}")
    return var
