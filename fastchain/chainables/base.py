"""
This module contains the base implementation of ChainableBase interface,
any other chainable should be inheriting from Chainable class that
provides basic functionalities.

The module also implements the node chainable (the component that wraps function),
and the skipping component called pass
"""

from abc import ABC
from functools import partial, partialmethod
from typing import TypeAlias, Any, Callable, TypeVar, ParamSpec, Literal

from .._abc import ChainableBase, ReporterBase
from .._tools import camel_to_snake

T = TypeVar('T')
SPEC = ParamSpec('SPEC')
RT = TypeVar('RT')
ChainableObject = TypeVar('ChainableObject', bound='Chainable', covariant=True)  # preserves the same chainable type
FEEDBACK: TypeAlias = tuple[bool, T]
CHAINABLE: TypeAlias = Callable[[Any], Any]


class Chainable(ChainableBase, ABC):
    """base class for all chainable elements."""
    __slots__ = 'name', 'title', 'optional',
    NAME: str

    def __init_subclass__(cls, type_name: str | None = None, **kwargs):
        """
        creates the object default name when a subclass of Chainable
        is defined by converting the CamelCase to snake_case if no
        custom name is provided like:

        >>> class ChainableSubclass(Chainable, type_name="custom_name"):
        ...     ... # implementation goes here

        :param type_name: the default name
        :type type_name: str
        """
        if type_name is None:
            type_name = camel_to_snake(cls.__name__)
        cls.NAME = type_name

    def __init__(self, name: str | None = None) -> None:
        if name is None:
            name = self.NAME
        self.name = name
        self.title = name
        self.optional = False

    def __repr__(self): return f'<Chain{type(self).__name__}: {self.name}>'
    def __len__(self): return 0

    def set_title(self, root: str | None = None, branch: str | None = None) -> None:
        """
        creates the chain's coll_title with a uniform format.

        + If no root is given -> 'name'
        + If only name and root are given -> 'root/name'
        + If name, root and branch are given -> 'root[branch]/name'

        :param root: pre-generated root coll_title if exists
        :type root: str | None
        :param branch: index or key of the root branch identifying this chainable
        :type branch: str | None
        :return: root[branch]/sub_root[sub_branch]/.../name ...
        :rtype: str
        """
        if root is None:
            self.title = self.name
        else:
            if branch is not None:
                root = f'{root}[{branch}]'
            self.title = f'{root}/{self.name}'

    def failure(self, input: Any, error: Exception, report: ReporterBase) -> None:
        """
        marks current operation as failure.

        :param input: the value that caused the failure.
        :param error: the exception that caused the failure.
        :param report: reporter object that holds processing details.
        """
        report.register_failure(self.title, input, error, not self.optional)


class Pass(Chainable):
    """
    PASS object is a chainable that does nothing but passing the received value as it is.
    this was originally created to be used for branching (model, group or match),
    where a branch only needs to pass the value as it is, this component
    never fails, and it's more optimized than Node(lambda x: x)
    """
    def process(self, input: T, report: ReporterBase) -> tuple[Literal[True], T]:
        return True, input

    def __repr__(self) -> str: return '<chain-pass>'

    def set_title(self, root: str | None = None, branch: str | None = None):
        """PASS ignores title modification"""

    def default_factory(self) -> None:
        """this will never be used"""


class Node(Chainable):
    """
    chain's node is the main chainable, it's wraps a user defined 1-argument function.
    if this function raises an exception when called with a value, the exception
    is stored and reported without affecting the main program and the node
    process is marked as failure.
    """
    __slots__ = 'function', 'default'

    def __init__(self, function: Callable[SPEC, RT], *, name: str | None = None, default: T = None) -> None:
        if name is None:
            name = self.get_qualname(function)
        elif not isinstance(name, str):
            raise TypeError(f"node's name must be str not {type(name)}")
        elif not name:
            raise ValueError("node's name cannot be empty")
        if not callable(function):
            raise TypeError(f"node's function must be callable with signature (Any) -> Any, not {type(function)}")
        super().__init__(name)
        self.function = function
        self.default: T = default

    def default_factory(self) -> T:
        """generates the default value, None by default"""
        return self.default

    def __len__(self): return 1

    @classmethod
    def get_qualname(cls, function: Callable) -> str:
        """gets the function's qualified name"""
        if isinstance(function, (partial, partialmethod)):
            return cls.get_qualname(function.func)
        elif hasattr(function, '__qualname__'):
            return getattr(function, '__qualname__')
        else:
            return f"{getattr(type(function), '__qualname__')}_object"

    def process(self, input, report: ReporterBase) -> tuple[True, RT] | tuple[False, T]:
        try:
            result = self.function(input)
        except Exception as error:
            report(self, False)
            self.failure(input, error, report)
            return False, self.default_factory()
        report(self, True)
        return True, result
