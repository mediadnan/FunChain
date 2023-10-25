import asyncio
import functools
import re
from typing import Callable, ParamSpec, Coroutine, TypeVar


SPEC = ParamSpec('SPEC')
RT = TypeVar('RT')


def is_async(func: Callable) -> bool:
    """
    Checks if the function / callable is defined as asynchronous

    :param func: The function to be checked
    :return: True if function is async else returns False
    """
    # Inspired from the Starlette library
    # https://github.com/encode/starlette/blob/4fdfad20abf8981e15babe015eb5d8330d9c7662/starlette/_utils.py#L13
    while isinstance(func, functools.partial):
        func = func.func
    return asyncio.iscoroutinefunction(func) or asyncio.iscoroutinefunction(getattr(func, '__call__', None))


def asyncify(func: Callable[SPEC, RT], /) -> Callable[SPEC, Coroutine[None, None, RT]]:
    """
    Wraps blocking function to be called in a separate loop's (default) executor

    :param func: The function to be asyncified
    :return: async version of function
    """

    @functools.wraps(func)
    async def async_func(*args: SPEC.args, **kwargs: SPEC.kwargs) -> Coroutine[None, None, RT]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    return func if is_async(func) else async_func


def pascal_to_snake(name: str) -> str:
    """converts PascalCase names to snake_case names"""
    assert isinstance(name, str), "name must be a string"
    # CamelCase to snake_case (source of code)
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)


def validate_name(name: str) -> None:
    """Ensures that the name is valid"""
    if not isinstance(name, str):
        raise TypeError(f"name must be {str}")
    elif not name.isidentifier():
        raise ValueError(f"{name!r} is not a valid name")


def get_function_name(fun: Callable, /) -> str:
    """Gets the function's name"""
    try:
        name = fun.__name__
        if name == '<lambda>':
            name = 'lambda'
    except AttributeError:
        name = type(fun).__name__
    return pascal_to_snake(name)
