"""Module that contains utility function concerning function, node, and chain names"""
import re
import types
import typing
import inspect
import functools


NAME_SEPARATOR = '.'
SAME_NAME_SEP = '_'


def pascal_to_snake(name: str) -> str:
    """converts PascalCase names to snake_case names"""
    assert isinstance(name, str), "name must be a string"
    # CamelCase to snake_case (source of code)
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)


CallerNamePattern = re.compile(r'\s*(?P<name>[\w_.-]+)\s*=')


def guess_var_name(stack_level: int = 2) -> str | None:
    """
    Gets the name of the called object from the stack frame,
    this function is meant to be called inside the function call.
    However, if the function is called from a deeper level,
    a higher stack_level number should be specified.
    """
    try:
        return inspect.stack()[stack_level - 1:][0].function
    except (LookupError, AttributeError, TypeError):
        return


def get_module_name(obj) -> str | None:
    """Gets the name of the module owning the object"""
    if (module_name := getattr(obj, '__module__', None)) and module_name and module_name != '__main__':
        return module_name


def get_func_name(func: types.FunctionType | typing.Callable) -> str:
    """Gets the name of the function"""
    module_name = get_module_name(func)
    while isinstance(func, functools.partial):
        func = func
    try:
        name = func.__qualname__
    except AttributeError:
        name = pascal_to_snake(type(func).__qualname__)
    names = name.split(NAME_SEPARATOR)
    if module_name is not None:
        names = module_name.split(NAME_SEPARATOR) + names
    return SAME_NAME_SEP.join(names)


def validate(name: str) -> None:
    """Ensures that the name is valid"""
    if not isinstance(name, str):
        raise TypeError(f"name must be {str}")
    elif not name.isidentifier():
        raise ValueError(f"{name!r} is not a valid name")
