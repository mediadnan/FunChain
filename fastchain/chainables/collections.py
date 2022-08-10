"""
This module implements Chainable collections, those are containers
containing node components or another nested containers, they process
data by passing the input to their members and return the results
in a specific format.
"""
from abc import ABC
from typing import TypeVar, overload, Any, Generator
from .base import Chainable
from .._abc import ReporterBase

ChainableCollection = TypeVar('ChainableCollection', bound='Collection', covariant=True)


class Collection(Chainable, ABC):
    """
    Collection is the base class for all chainable-collection objects,
    and those are objects that contain another chainables that actually
    do the processing and the collection only orchestrates this process.
    """
    __slots__ = 'branches', 'members',

    @overload
    def __init__(self, *members: Chainable) -> None: ...
    @overload
    def __init__(self, **members: Chainable) -> None: ...

    def __init__(self, *args, **kwargs):
        super(Collection, self).__init__()
        if args and kwargs:
            raise ValueError("cannot pass positional and keyword members together")
        elif not (args or kwargs):
            raise ValueError(f"{self.NAME} cannot be created without members")

        branches, members = zip(*enumerate(args)) if args else zip(*kwargs.items())

        if not all((isinstance(member, Chainable) for member in members)):
            raise TypeError("all members must be of type chainable")
        self.branches: tuple[str, ...] = tuple(map(str, branches))
        self.members: tuple[Chainable, ...] = tuple(members)

    def __len__(self):
        return sum(len(member) for member in self.members)

    def set_title(self, root: str | None = None, branch: str | None = None):
        super(Collection, self).set_title(root, branch)
        for branch, member in zip(self.branches, self.members):
            member.set_title(self.title, branch)


class Sequence(Collection):
    """
    chain's sequence is a chainable collection that processes data sequentially
    from a member to the next in the same order passed to the constructor.

    the chain's sequence ignores failures from optional members and forwards
    their input to the next member as it is, however if a required
    member fails, the sequence fails and returns that member's default value.
    """

    def default_factory(self) -> Any:
        """gets the default value from the last required member"""
        default = None
        for member in reversed(self.members):
            if not member.optional:
                default = member.default_factory()
                break
        return default

    def process(self, input, reporter: ReporterBase) -> tuple[bool, Any]:
        success_set: set[bool] = set()
        for node in self.members:
            success, result = node.process(input, reporter)
            if success:
                input = result
            elif not node.optional:
                return False, self.default_factory()
            success_set.add(success)
        return any(success_set), input


class Match(Collection):
    """
    chain's match is a chainable collection that provides different processing
    branch for each item in the given input, it is stricter than the rest of
    it siblings (Collection) and requires you to know exactly what data you're
    going to get, if it gets a non-iterable object or an iterable with a different
    size than its members (branches) it immediately fails.

    chain's match object processes data by iterating over input items and its
    internal members simultaneously and passes each item to the corresponding
    member, the processing will also fail any member has failed.
    """

    def default_factory(self) -> Any:
        """generates an iterator of default value for each member"""
        for member in self.members:
            yield member.default_factory()

    def _process(self, args, reporter: ReporterBase, states: set[bool]) -> Generator[Any, None, None]:
        try:
            args_members = tuple(zip(args, self.members, strict=True))
        except Exception as error:
            self.failure(args, error, reporter)
            yield from self.default_factory()
        else:
            for arg, node in args_members:
                success, result = node.process(arg, reporter)
                states.add(success)
                yield result

    def process(self, args, reporter: ReporterBase) -> tuple[bool, tuple]:
        states: set[bool] = set()
        results: tuple = tuple(self._process(args, reporter, states))
        success = (states == {True})
        return success, results


class Model(Collection, ABC):
    """
    Models are chainable collection objects that return
    the processing result with the same structure as
    it was defined, a dict_model returns a dict, list_model
    returns a list ...
    """


class ListModel(Model):
    """
    chain's list-model is a chainable collection that processes
    the input by passing it to each of it members and returns
    the list of results with the same definition order.

    the list-model will fail if none of it members succeed or
    if a required member fails, and failing optional members
    will be simply skipped.
    """

    def default_factory(self) -> Any:
        """generates a list of default values from required members"""
        return [member.default_factory() for member in self.members if not member.optional]

    def process(self, input, reporter: ReporterBase) -> tuple[bool, list]:
        successes: set[bool] = set()
        results: list = list()
        for member in self.members:
            success, result = member.process(input, reporter)
            if success or not member.optional:
                successes.add(success)
                results.append(result)
        return (successes == {True}), results


class DictModel(Model):
    """
    chain's dict-model is a chainable collection that processes
    the input by passing it to each of it members and returns
    the dict mapping each key to its results.

    the dict-model will fail if none of it members succeed or
    if a required member fails, and failing optional members
    will be simply skipped.
    """

    def default_factory(self) -> Any:
        """generates a dict of default values from required members"""
        return {
            branch: member.default_factory()
            for branch, member in zip(self.branches, self.members)
            if not member.optional
        }

    def process(self, input, reporter: ReporterBase) -> tuple[bool, dict]:
        successes: set[bool] = set()
        results: dict[str, Any] = dict()
        for branch, member in zip(self.branches, self.members):
            success, result = member.process(input, reporter)
            if success or not member.optional:
                successes.add(success)
                results[branch] = result
        return (successes == {True}), results
