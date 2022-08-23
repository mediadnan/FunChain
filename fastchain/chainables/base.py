"""
This module implements the Chainable abstract base class which contains basic functionalities
that every chain component should have, it also implements the main Chainable component called Node,
which is a wrapper around user functions the runs them in try...except blocks and report the processing details.
"""

from abc import ABC
from functools import partial, partialmethod
from typing import TypeAlias, Any, Callable, TypeVar, Literal

from .._abc import ChainableBase, ReporterBase
from .._tools import camel_to_snake

T = TypeVar('T')
RT = TypeVar('RT')
ChainableObject = TypeVar('ChainableObject', bound='Chainable', covariant=True)  # preserves the same chainable type
FEEDBACK: TypeAlias = tuple[bool, T]
CHAINABLE: TypeAlias = Callable[[Any], Any]


class Chainable(ChainableBase, ABC):
    """abstract base class for all chain components"""
    __slots__ = 'name', 'title', 'optional', 'required'

    def __init_subclass__(cls, default_name: str | None = None, **kwargs):
        """defines the object default name for each subclass.

        When a class extends Chainable class, the default 'default_name'
        is the class name (ChainableSubclass.__name__) converted
        from 'CamelCase' to 'snake_case', but it can be also explicitly
        set when defining the ChainableSubclass like so:

        >>> class ChainableSubclass(Chainable, default_name="custom_name"):
        ...     ... # implementation goes here

        :param default_name: the default name if no name is given
        :type default_name: str
        """
        if default_name is None:
            default_name = camel_to_snake(cls.__name__)
        cls.NAME = default_name

    def __init__(self, name: str | None = None) -> None:
        """sets the default values when the component is created.

        :param name: component name
        :type name: str
        """
        if name is None:
            name = self.NAME
        self.name = name
        self.title = name
        self.optional = False
        self.required = True

    def __repr__(self):
        """gets the component's string representation"""
        return f'<Chain{type(self).__name__}: {self.name}>'

    def __len__(self):
        """gets the component's size"""
        return 0

    def set_title(self, root: str | None = None, branch: str | None = None) -> None:
        """creates the chain's nodes title with a uniform format.

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

    def failure(self, input: Any, error: Exception, reporter: ReporterBase) -> None:
        """convenient way for components to report failures to the given reporter

        :param input: value that caused the failure
        :param error: exception object raised
        :param reporter: reporter that holds the current processing info
        """
        reporter.report_failure(self, input, error)


class Pass(Chainable):
    """
    PASS is a chainable object that does nothing but passing the given value as it is.
    this was originally created for models with a branch that needs to pass the input as it is,
    and it is a slightly optimized version of Node(lambda x: x)
    """
    def process(self, input: T, reporter: ReporterBase) -> tuple[Literal[True], T]:
        """forwards the same input with success flag"""
        return True, input

    def __repr__(self) -> str:
        return '<chain-pass>'

    def set_title(self, root: str | None = None, branch: str | None = None):
        """PASS ignores title modification"""
        pass

    def default_factory(self) -> None:
        """this will never be used"""
        pass


PASS = Pass('pass')  # chains only need one instance of Pass (singleton)


class Node(Chainable):
    """
    Nodes are the main chain components, they wrap regular functions (and any callables)
    with only one required positional argument into chain nodes that have a name
    and execute in an isolated context keeping potential errors (side effects) from breaking
    the whole program, and report execution details.
    """
    __slots__ = 'function', 'default'

    def __init__(self, function: Callable[..., RT], *, name: str | None = None, default: T = None) -> None:
        """sets the main function to be wrapped and optionally a name and a default value

        :param function: 1-argument function to be wrapped
        :type function: (Any) -> Any
        :param name: name of the node (default function.__qualname__)
        :type name: str
        :param default: value to be returned when failing (default None)
        :type default: Any
        """
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

    def __len__(self):
        """node's size is always 1, nodes are the units."""
        return 1

    @classmethod
    def get_qualname(cls, function: Callable) -> str:
        """gets the function's qualified name for a default name"""
        if isinstance(function, (partial, partialmethod)):
            return cls.get_qualname(function.func)
        elif hasattr(function, '__qualname__'):
            return getattr(function, '__qualname__')
        else:
            return f"{getattr(type(function), '__qualname__')}_object"

    def process(self, input, reporter: ReporterBase) -> tuple[True, RT] | tuple[False, T]:
        """
        runs function(input) in isolation and returns the result
        or the default if any error occurs,

        the node uses the given reporter to mark the execution
        success state and report failures if they occur.

        :param input: an input object that function expects
        :type input: Any
        :param reporter: the reporter that holds the current execution info
        :type reporter: ReporterBase
        :return: success state and the call result
        :rtype: tuple[bool, Any]
        """
        try:
            result = self.function(input)
        except Exception as error:
            reporter.mark(self, False)
            self.failure(input, error, reporter)
            return False, self.default_factory()
        reporter.mark(self, True)
        return True, result
