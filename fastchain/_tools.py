"""This module contains shared utility functions used by the FastChain modules"""

import re
from typing import Callable, Any


def camel_to_snake(name: str) -> str:
    """
    converts CamelCase (class name style) to snake_case (instance name style)

    :param name: CamelCase name
    :type name: str
    :return: snake_case name
    :rtype: str
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower()


def bind(obj, method: Callable[..., Any], method_name: str | None = None) -> None:
    """
    dynamically assign a method to an object.

    :param obj: Any mutable object that allows 'setattr'
    :param method: a function with signature (self, ...) -> Any
    :type method: function
    :param method_name: name given to the assign method, default method.__name__
    :type method_name: str
    :return: None
    """
    if method_name is None:
        method_name = method.__name__
    setattr(obj, method_name, getattr(method, '__get__')(obj, obj.__class__))
