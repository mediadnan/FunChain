from abc import ABC
from functools import partial, partialmethod
from typing import (
    TypeAlias,
    Any,
    Callable,
    TypeVar,
)

from .._abc import ChainableBase, ReporterBase

T = TypeVar('T')
ChainableObject = TypeVar('ChainableObject', bound='Chainable', covariant=True)
FEEDBACK: TypeAlias = tuple[bool, T]
CHAINABLE: TypeAlias = Callable[[Any], Any]


class Chainable(ChainableBase, ABC):
    """base class for all chainable elements."""
    __slots__ = 'name', 'title', 'optional',

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.title: str = name
        self.optional: bool = False

    def __repr__(self):
        return f'<chain-{type(self).__name__.lower()}: {self.name}>'

    def set_title(self, root: str | None = None, branch: str | None = None) -> None:
        """
        creates the chain's title with a uniform format.

        + If no root is given -> 'name'
        + If only name and root are given -> 'root/name'
        + If name, root and branch are given -> 'root[branch]/name'

        :param root: pre-generated root title if exists
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
        :param report: report object that holds processing details.
        """
        report.register_failure(self.title, input, error, not self.optional)


class Pass(Chainable):
    """
    a pass is a chainable that does nothing but passing the received value as it is.
    this was originally created to be used in branching (model, group) or matching (match),
    where a branch only needs to pass the value as it is, this component
    never fails, and it's more optimized than a node with lambda x: x
    """
    def process(self, input: T, report: ReporterBase) -> FEEDBACK[T]:
        return True, input

    def __repr__(self) -> str:
        return '<chain-pass>'

    def set_title(self, root: str | None = None, branch: str | None = None):
        """PASS ignores the title"""
        pass


class Node(Chainable):
    """
    a node is the main chainable, it's wraps a user defined 1-argument function.
    if this function raises an exception when called with a value, the exception
    is stored and reported without affecting the main program and the node
    process is marked as failure.
    """
    __slots__ = 'function', 'default_factory',

    def __init__(
            self,
            function: CHAINABLE, *,
            name: str | None = None,
            default: Any = None,
            default_factory: Callable[[], Any] | None = None
    ) -> None:
        if name is None:
            name = self.get_qualname(function)
        elif not isinstance(name, str):
            raise TypeError(f"node's name must be str not {type(name)}")
        elif not name:
            raise ValueError("node's name cannot be empty")
        super().__init__(name)
        if not callable(function):
            raise TypeError(f"node's function must be callable with signature (Any) -> Any, not {type(function)}")
        self.function: CHAINABLE = function
        if default_factory is None:
            def df(): return default
            default_factory = df
        elif not callable(default_factory):
            raise TypeError("default_factory must be a 0-argument callable that returns any value")
        self.default_factory: Callable[[], Any] = default_factory

    @classmethod
    def get_qualname(cls, function: Callable) -> str:
        """gets the function's qualified name"""
        if isinstance(function, (partial, partialmethod)):
            return cls.get_qualname(function.func)
        elif hasattr(function, '__qualname__'):
            return getattr(function, '__qualname__')
        else:
            return f"{getattr(type(function), '__qualname__')}_object"

    def process(self, input, report: ReporterBase) -> FEEDBACK:
        try:
            result = self.function(input)
        except Exception as error:
            report(self, False)
            self.failure(input, error, report)
            return False, self.default_factory()
        report(self, True)
        return True, result


def optional(chainable: ChainableObject) -> ChainableObject:
    """sets the chainable as optional"""
    chainable.optional = True
    return chainable
