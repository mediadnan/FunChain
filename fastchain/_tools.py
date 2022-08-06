import re
from functools import partialmethod, partial
from typing import Pattern, Callable

NAME: Pattern[str] = re.compile(r'^[a-z_](?:\w+[_-]?)+?$', re.IGNORECASE)


def get_qualname(func: Callable) -> str:
    """gets the object's (function's) qualified name"""
    if isinstance(func, (partial, partialmethod)):
        return get_qualname(func.func)
    elif hasattr(func, '__qualname__'):
        return getattr(func, '__qualname__')
    else:
        return f"{getattr(type(func), '__qualname__')}_object"


def validate_name(name: str) -> str:
    """validates the component name"""
    if not isinstance(name, str):
        raise TypeError(f"name must be str not {type(name).__name__}")
    elif not NAME.match(name):
        raise ValueError("the name should start with a letter and only contain letters, digits, '_' , and '-'")
    return name
