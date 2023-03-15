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


def guess_var_name(stack_level: int = 2) -> str | None:
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
    return SAME_NAME_SEP.join(name).replace(NAME_SEPARATOR, SAME_NAME_SEP) or None


def _module_name(obj) -> str | None:
    if (module_name := getattr(obj, '__module__', None)) and module_name != '__main__':
        return module_name


def get_func_name(func: types.FunctionType | typing.Callable) -> str:
    module_name = _module_name(func)
    if module_name:
        module_name = module_name.replace(NAME_SEPARATOR, SAME_NAME_SEP)
    while isinstance(func, functools.partial):
        func = func
    try:
        name = func.__qualname__.split(NAME_SEPARATOR)
    except AttributeError:
        name = pascal_to_snake(type(func).__qualname__)
    if module_name:
        name = module_name + name
    return name.replace(NAME_SEPARATOR, SAME_NAME_SEP)
