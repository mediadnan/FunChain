import abc
from typing import (
    Any,
    TypeAlias,
    Iterable,
    Callable,
    Generator,
    Type,
    TypeVar
)

from .monitoring import Report

FEEDBACK: TypeAlias = tuple[bool, Any]
CHAINABLE: TypeAlias = Callable[[Any], Any]
CHAINABLE_OBJECTS: TypeAlias = CHAINABLE | tuple | dict[str | int, Any] | list | str


def iter_chainable(cls: Type['CT']) -> Type['CT']:
    if not issubclass(cls, Chainable):
        raise TypeError(f"this option only works on {Chainable} subclasses.")

    class Map(cls, abc.ABC):    # type: ignore
        def __call__(self, args, report: Report) -> FEEDBACK:
            try:
                iter(args)
            except TypeError as error:
                self.failure(args, error, report)
                return False, None
            return True, self._process(args, report)

        def _process(self, args: Iterable, report: Report) -> Generator[Any, None, None]:
            for arg in args:
                success, result = super(Map, self).__call__(arg, report)
                if success:
                    yield result
    Map.__name__ = f"{cls.__name__}*"
    return Map


class Chainable(abc.ABC):

    __slots__ = 'title', 'optional', '__repr'

    def __new__(cls, *args, iterable: bool = False, **kwargs):
        return super().__new__(iter_chainable(cls) if iterable else cls)

    def __init__(self, *, title: str, optional: bool = False, **_):
        self.title: str = title
        self.optional: bool = optional
        self.__repr: str = f"<chain-{self.__class__.__name__.lower()}>"

    def __repr__(self) -> str:
        return self.__repr

    @abc.abstractmethod
    def __call__(self, input, report: Report) -> FEEDBACK:
        """
        processes arg and returns feedback with success and result.

        :param input: the input value to be processed.
        :param report: report object that holds processing details.
        """

    @abc.abstractmethod
    def nodes(self) -> Generator['Node', None, None]:
        """iterates over internal chain nodes."""
    def failure(self, input: Any, error: Exception, report: Report) -> None:
        """
        marks current operation as failure.

        :param input: the value that caused the failure.
        :param error: the exception that caused the failure.
        :param report: report object that holds processing details.
        """
        report.register_failure(self.title, input, error)


class Node(Chainable):
    """
    a node is the main chainable, it's wraps a user defined 1-argument function.
    if this function raises an exception when called with a value, the exception
    is stored and reported without affecting the main program and the node
    process is marked as failure.
    """

    __slots__ = 'function', 'default_factory'

    def __init__(
            self,
            function: CHAINABLE,
            *,
            default: Any = None,
            default_factory: Callable[[], Any] = None,
            **kwargs,
    ):
        super(Node, self).__init__(**kwargs)
        self.function: CHAINABLE = function
        self.default_factory: Callable[[], Any] = default_factory if callable(default_factory) else lambda: default

    def __call__(self, input, report: Report) -> FEEDBACK:
        try:
            result = self.function(input)
        except Exception as error:
            self.failure(input, error, report)
            report(self, False)
            return False, self.default_factory()
        report(self, True)
        return True, result

    def nodes(self) -> Generator['Node', None, None]:
        yield self


class Collection(Chainable, abc.ABC):
    """
    a collection is a chainable that contains other chainables called members,
    it must implement a way of passing the input to its members according to it expected behaviour.
    """

    __slots__ = 'members',

    def __init__(self, members: Iterable[Chainable], **kwargs):
        if 'optional' not in kwargs:
            kwargs['optional'] = all(node.optional for node in members)
        super(Collection, self).__init__(**kwargs)
        self.members: tuple[Chainable, ...] = tuple(members)

    def nodes(self) -> Generator['Node', None, None]:
        for node in self.members:
            yield from node.nodes()


class Pipe(Collection):
    """
    a pipe is a chainable that contains a series of chainables, when called with a value
    it passes the result to the first chainable and its result is passed to the next until
    the last one.
    if an optional chainable fails, its input will be passed as it is to the next one,
    however if a required chainable fails, the whole pipe fails.
    """
    def __call__(self, input, report: Report) -> FEEDBACK:
        for node in self.members:
            success, result = node(input, report)
            if success:
                input = result
            elif not node.optional:
                return False, result
        return True, input


class Match(Collection):
    """
    a match is a matching chainable that holds multiple branches, if called with an iterable
    with the same size of its branches, it applies each branch to the corresponding value.
    however if any of the following cases happen
    (the size is not the same, the value given is not iterable or
    branch fails, no matter if it's optional or required)
    the match process is marked as failure.
    """
    def __call__(self, args: Iterable, report: Report) -> FEEDBACK:
        results: list = list()
        try:
            for arg, node in zip(args, self.members, strict=True):
                success, result = node(arg, report)
                if not success:
                    return False, None
                results.append(result)
            return True, results
        except Exception as error:
            self.failure(args, error, report)
            return False, None


class Group(Collection):
    """
    a group is a branching chainable that holds ordered branches,
    when called it passes the value to each of its branch members and returns a list
    of successful results with the same order.
    if an optional branch fails it will be skipped, and if a required branch fails,
    the group process is marked as failure.
    """
    def __call__(self, input, report: Report) -> FEEDBACK:
        successes: set[bool] = set()
        results: list = list()
        for node in self.members:
            success, result = node(input, report)
            if not success and node.optional:
                continue
            successes.add(success)
            results.append(result)
        if any(successes):
            return True, results
        return False, None


class Model(Collection):
    """
    a model is a branching chainable that holds named branches,
    when called it passes the value to each of its branch members and returns a dictionary
    with the same names and the successful values.
    if an optional branch fails it will be skipped together with it name,
    and if a required branch fails, the model process is marked as failure.
    """

    __slots__ = 'keys',

    def __init__(self, model: dict[Any, Chainable], **kwargs):
        self.keys, members = zip(*model.items())
        super().__init__(members, **kwargs)

    def __call__(self, input, report: Report) -> FEEDBACK:
        successes: set[bool] = set()
        results: dict = dict()
        for key, node in zip(self.keys, self.members):
            success, result = node(input, report)
            if not success and node.optional:
                continue
            successes.add(success)
            results[key] = result
        if any(successes):
            return True, results
        return False, None


class Pass(Chainable):
    """
    a pass is a chainable that does nothing but passing the received value as it is.
    this was originally created to be used in branching (model, group) or matching (match),
    where a branch only needs to pass the value as it is, this component
    never fails, and it's more optimized than a node with lambda x: x
    """
    def __call__(self, input, report: Report) -> FEEDBACK:
        return True, input

    def nodes(self) -> Generator['Node', None, None]:
        yield from ()


PASS = Pass(title='pass')                               # pass instance (as singleton)
CT = TypeVar('CT', bound=Chainable, covariant=True)     # chainable type
CCT = TypeVar('CCT', bound=Collection, covariant=True)  # chainable collection type
