import asyncio
import functools
from typing import Callable, ParamSpec, Coroutine, TypeVar


SPEC = ParamSpec('SPEC')
RT = TypeVar('RT')


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
