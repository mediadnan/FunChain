import functools
import typing

from .elements import Chainable, CHAINABLE_FUNC_TYPE


def chainable(name: str):
    """converts a normal function to a named reusable process"""
    def decorated(func_gen: typing.Callable[..., CHAINABLE_FUNC_TYPE]):
        @functools.wraps(func_gen)
        def wrapper(*args, multiple_results: bool = False, **kwargs):
            return Chainable(name, func_gen(*args, **kwargs), multiple=multiple_results)
        return wrapper
    return decorated
