"""
This module implement different types of chainable collections,
those are node-like objects that contain multiple nodes or/and also
other nested collection, they all share similar properties and process
data by passing it to their branches and bundle results in a specific structure.
"""
from abc import ABC
from typing import TypeVar, overload, Any, Generator, Iterable

from .base import Chainable
from .._abc import ReporterBase


ChainableCollection = TypeVar('ChainableCollection', bound='Collection', covariant=True)


class Collection(Chainable, ABC):
    """abstract base class for all the chainable collections"""
    __slots__ = 'branches', 'members',

    @overload
    def __init__(self, *members: Chainable) -> None: ...
    @overload
    def __init__(self, **members: Chainable) -> None: ...

    def __init__(self, *args, **kwargs):
        """populates the collection with the given members either with or without branch names"""
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
        """collection size is defined by how many nodes it contains (recursively)"""
        return sum(len(member) for member in self.members)

    def set_title(self, root: str | None = None, branch: str | None = None):
        super().set_title(root, branch)
        for branch, member in zip(self.branches, self.members):
            member.set_title(self.title, branch)


class Sequence(Collection):
    """
    The sequence is a chainable that processes data sequentially
    piping results from one member to the next in the same order passed to the constructor.

    the sequence ignores failures from optional members and forwards
    their input to the next member as it is, however if a required
    member fails, the sequence fails and returns that member's default.
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
        """
        pipes the input from a member to the next by chaining .process
        calls until the last one.

        It uses the given reporter to report failures if they occur.

        :param input: initial value to start a chain of process calls
        :type input: Any
        :param reporter: reporter that holds the current execution info
        :type reporter: ReporterBase
        :return: success state and the last result (or default in case of failures)
        :rtype: tuple[bool, Any]
        """
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
    The match is a chainable that provides different processing
    branch for each item in the given input, it is stricter than the rest of
    it siblings (Collection) and requires you to know exactly what data you're
    going to get, if it gets a non-iterable object or an iterable with a different
    size than its members (branches) it immediately fails.

    the match object processes data by iterating over input items and its
    internal members simultaneously and passes each item to the corresponding
    member, the processing will also fail any member has failed.
    """

    def default_factory(self) -> Any:
        """generates an iterator of default value for each member"""
        return tuple(member.default_factory() for member in self.members)

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

    def process(self, args: Iterable, reporter: ReporterBase) -> tuple[bool, tuple]:
        """
        passes each arg from args to a specific member with the same order

        :param args: an iterable object (list, tuple, set, ...)
        :type args: Iterable
        :param reporter: reporter that holds the current execution info
        :type reporter: ReporterBase
        :return: success state and a tuple of results with the same order
        :rtype: tuple[bool, tuple]
        """
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

    This base class does nothing currently, but it's a logical
    ancestor for all models if they need to share functionality
    in the future.
    """


class ListModel(Model):
    """
    The list-model is a chainable that processes
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
    The dict-model is a chainable that processes
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
