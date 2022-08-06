from abc import ABC
from typing import TypeVar, overload
from .base import Chainable, FEEDBACK
from ..monitoring import Reporter


ChainableCollection = TypeVar('ChainableCollection', bound='Collection', covariant=True)


class Collection(Chainable, ABC):
    """
    a collection is a chainable that contains other chainables called members,
    it must implement a way of passing the input to its members according to it expected behaviour.
    """

    __slots__ = 'branches', 'members',

    @overload
    def __init__(self, *members: Chainable) -> None: ...
    @overload
    def __init__(self, **members: Chainable) -> None: ...

    def __init__(self, *args, **kwargs):
        name = type(self).__name__.lower()
        super(Collection, self).__init__(name)
        if args and kwargs:
            raise ValueError("cannot pass positional and keyword members together")
        elif not (args or kwargs):
            raise ValueError(f"{name} cannot be created without members")

        branches, members = zip(*enumerate(args)) if args else zip(*kwargs.items())

        if not all((isinstance(member, Chainable) for member in members)):
            raise TypeError("all members must be of type chainable")
        self.branches: tuple[str, ...] = tuple(map(str, branches))
        self.members: tuple[Chainable, ...] = tuple(members)

    def set_title(self, root: str | None = None, branch: str | None = None):
        super(Collection, self).set_title(root, branch)
        for branch, member in zip(self.branches, self.members):
            member.set_title(self.title, branch)


class Sequence(Collection):
    """
    a sequence is a chainable that contains a series of chainables, when called with a value
    it passes the result to the first chainable and its result is passed to the next until
    the last one.
    if an optional chainable fails, its input will be passed as it is to the next one,
    however if a required chainable fails, the whole sequence fails.
    """

    def process(self, input, report: Reporter) -> FEEDBACK:
        for node in self.members:
            success, result = node.process(input, report)
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
    def process(self, args, report: Reporter) -> FEEDBACK:
        results: list = list()
        try:
            for arg, node in zip(args, self.members, strict=True):
                success, result = node.process(arg, report)
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
    def process(self, input, report: Reporter) -> FEEDBACK:
        successes: set[bool] = set()
        results: list = list()
        for node in self.members:
            success, result = node.process(input, report)
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

    def process(self, input, report: Reporter) -> FEEDBACK:
        successes: set[bool] = set()
        results: dict = dict()
        for key, node in zip(self.branches, self.members):
            success, result = node.process(input, report)
            if not success and node.optional:
                continue
            successes.add(success)
            results[key] = result
        if any(successes):
            return True, results
        return False, None
