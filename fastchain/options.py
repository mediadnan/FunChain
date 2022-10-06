"""
This module contains the implementation of functions that mutates nodes.
"""
from typing import Callable, TypeAlias, Any

from .nodes import Node, Loop


OptionsType: TypeAlias = Callable[[Node], Node]


def _bind(obj, method: Callable[..., Any], method_name: str | None = None) -> None:
    """
    Dynamically assigns a method to an object.

    :param obj: Any object that allows 'setattr'
    :param method: Function with signature (self, ...) -> Any
    :param method_name: Name given to the assign method, default method.__name__
    """
    if method_name is None:
        method_name = method.__name__
    setattr(obj, method_name, getattr(method, '__get__')(obj, obj.__class__))


def optional(node: Node) -> Node:
    """Makes the node optional"""
    node.optional = True
    return node


def set_default(node: Node, default=None, default_factory: Callable[[], Any] | None = None) -> Node:
    """Sets a custom default value to the given node"""
    if default_factory is not None:
        if not callable(default_factory):
            raise TypeError("default_factory must be a 0-argument callable")
        _bind(node, lambda self: default_factory(), 'default')
    elif default is not None:
        _bind(node, lambda self: default, 'default')
    return node


OPTIONS: dict[str, OptionsType] = {
    '?': optional,
    '*': Loop,
}
