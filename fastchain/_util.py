"""fastchain._util.py module implements internal fastchain utility functions"""
import functools
import re
import asyncio
import inspect
from typing import Callable, ParamSpec, TypeVar, Coroutine


def get_name(func: Callable, strip: str = '_') -> str:
    """
    Gets the functions name

    :param func: function with a name
    :param strip: whether to strip
    :return: the name
    """
    while isinstance(func, functools.partial):
        func = func.func
    name: str = getattr(func, '__name__', type(func).__name__)
    return name.strip(strip)


def get_varname(stack_level: int = 2) -> str | None:
    """
    Gets the fully qualified at assignment time.

    :param stack_level:
    :return: var_name or class.varname or class.inner.varname ...
    """
    stacks = inspect.stack()[stack_level:]
    name = []
    for stack in stacks:
        function_name = stack.function
        if function_name == '<module>':
            break
        name.append(function_name)
    name.reverse()
    context = stacks[0].code_context
    if context and (match := re.match(r'^\s*(?P<name>[A-Z_][\w_]*?)\s*=', context[0], re.IGNORECASE)):
        name.append(match.group('name'))
    return '.'.join(name) or None


def is_async(func: Callable) -> bool:
    """
    Checks if the function / callable is defined as asynchronous

    :param func: the function to be checked
    :return: True if function is async else False
    """
    # Inspired from the Starlette library
    # https://github.com/encode/starlette/blob/4fdfad20abf8981e15babe015eb5d8330d9c7662/starlette/_utils.py#L13
    while isinstance(func, functools.partial):
        func = func.func
    return asyncio.iscoroutinefunction(func) or asyncio.iscoroutinefunction(getattr(func, '__call__', None))


SPEC = ParamSpec('SPEC')
RT = TypeVar('RT')


def asyncify(func: Callable[SPEC, RT], /) -> Callable[SPEC, Coroutine[None, None, RT]]:
    """
    Wraps blocking function to be called in a separate loop's (default) executor

    :param func: the function to be asynchronified
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
