import abc
import logging
from typing import (
    Any,
    TypeAlias,
    TypeVar,
    Iterable,
    Callable,
    Generator,
    overload,
    Literal,
    Generic
)
from ._tools import get_qualname
from .monitoring import Report

T = TypeVar("T")
T1 = TypeVar('T1')
T2 = TypeVar('T2')
FEEDBACK: TypeAlias = tuple[Literal[True], T] | tuple[Literal[False], Any]
CHAINABLE: TypeAlias = Callable[[T1], T2]
CHAINABLE_OBJECTS: TypeAlias = CHAINABLE | tuple | dict[str | int, Any] | list | str


class Chainable(abc.ABC, Generic[T1, T2]):
    __slots__ = (
        'name',
        'title',
        'optional',
        'logger'
    )

    def __init__(
            self,
            *,
            name: str,
            title: str | None = None,
            optional: bool = False,
            root: str | None = None,
            pos: int | None = None,
            logger: logging.Logger | None = None,
    ):
        """
        initializes the chainable object.

        :param name: the component's name
        :param title: the full title roots.name[position]
        :param optional: True if the component is not required.
        :param root: root's title
        :param pos: position (index or key)
        :param logger: logger to be used.
        """
        if title is None:
            title = name
            if root is not None:
                title = f'{root}.{title}'
            if pos is not None:
                title = f'{title}[{pos}]'
        self.name: str = name
        self.title: str = title
        self.optional: bool = optional
        self.logger: logging.Logger | None = logger

    @abc.abstractmethod
    def __call__(self, input: T1, report: Report, index=None) -> FEEDBACK[T2]:
        """
        processes arg and returns feedback with success and result.

        :param input: the input value to be processed.
        :param report: report object that holds processing details.
        :param index: optionally a key or index in case of iteration.
        """

    @abc.abstractmethod
    def __repr__(self) -> str:
        """chainable string representation"""

    @abc.abstractmethod
    def nodes(self) -> Generator['ChainNode', None, None]:
        """iterates over internal chain nodes."""

    def failure(self, input: Any, error: Exception, report: Report, index=None) -> None:
        """
        marks current operation as failure.

        :param input: the value that caused the failure.
        :param error: the exception that caused the failure.
        :param report: report object that holds processing details.
        :param index: optionally a key or index in case of iteration.
        """
        title = self.title if index is None else f"{self.title}[{index}]"
        if self.logger is not None:
            self.logger.log(
                logging.DEBUG if self.optional else logging.ERROR,
                f"{title!r} failed with {error!r} from {input!r} (type: {type(input)})"
            )
        report.register_failure(title, {'input': input, 'error': error})


class ChainNode(Chainable):
    __slots__ = 'function', 'default_factory'

    def __init__(
            self,
            function: CHAINABLE[T1, T2],
            *,
            default: Any = None,
            default_factory: Callable[[], Any] | None = None,
            **kwargs
    ):
        if 'name' not in kwargs:
            kwargs['name'] = get_qualname(function)
        super().__init__(**kwargs)
        self.function: CHAINABLE = function
        self.default_factory: Callable[[], Any] = default_factory if callable(default_factory) else lambda: default

    def __call__(self, input: T1, report: Report, index=None) -> FEEDBACK[T2]:
        try:
            result = self.function(input)
        except Exception as error:
            self.failure(input, error, report, index)
            report(self, False)
            return False, self.default_factory()
        report(self, True)
        return True, result

    def __repr__(self) -> str:
        return f'<{self.name}>'

    def nodes(self) -> Generator['ChainNode', None, None]:
        yield self


class ChainOption(Chainable, abc.ABC):
    OPTION: str = NotImplemented

    __slots__ = 'node',

    def __init__(self, node: Chainable):
        super(ChainOption, self).__init__(title=node.title, name=f"{node.name}({self.OPTION})", optional=node.optional)
        self.node: Chainable = node

    def __repr__(self):
        return f"{self.node}({self.OPTION})"

    def nodes(self) -> Generator['ChainNode', None, None]:
        yield from self.node


class ChainMap(ChainOption):
    OPTION = '*'

    def __call__(self, args: Iterable[T1], report: Report, index=None) -> FEEDBACK[Iterable[T2]]:
        try:
            iter(args)
        except TypeError as error:
            self.failure(args, error, report, index)
            return False, None
        return True, self._process(args, report)

    def _process(self, args: Iterable, report: Report) -> Generator[Any, None, None]:
        for index, arg in enumerate(args):
            success, result = self.node(arg, report, index)
            if success:
                yield result


class ChainMapDict(ChainOption):
    OPTION = '*d'

    def __call__(self, arg: dict[T, Any], report: Report, index=None) -> FEEDBACK[dict[T, Any]]:
        if not isinstance(arg, dict):
            error = TypeError(f"{self.name} expects ")
            self.failure(arg, error, report, index)
            return False, None
        results = {}
        for key, value in arg.items():
            success, result = self.node(value, report, key)
            if not success:
                return False, None
            results[key] = result
        return True, results


class ChainCollection(Chainable, abc.ABC):
    NAME: str = 'chain-collection'
    __slots__ = 'members',

    def __init__(self, members: Iterable[Chainable], **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = self.NAME
        if 'optional' not in kwargs:
            kwargs['optional'] = all(node.optional for node in members)
        self.members: tuple[Chainable, ...] = tuple(members)
        super(ChainCollection, self).__init__(**kwargs)

    def nodes(self) -> Generator['ChainNode', None, None]:
        for node in self.members:
            yield from node.nodes()


class ChainSequence(ChainCollection):
    NAME = 'chain-sequence'

    def __call__(self, input, report: Report, index=None) -> FEEDBACK:
        for node in self.members:
            success, result = node(input, report, index)
            if success:
                input = result
            elif not node.optional:
                return False, result
        return True, input

    def __repr__(self):
        return ' -> '.join(map(repr, self.members))


class ChainModel(ChainCollection):
    NAME = 'chain-model'
    __slots__ = 'keys',

    def __init__(self, model: dict[T, Chainable], **kwargs):
        self.keys, nodes = zip(*model.items())
        super().__init__(nodes, **kwargs)

    def __call__(self, input, report: Report, index=None) -> FEEDBACK[dict[T, Any]]:
        successes: set[bool] = set()
        results: dict[T, Any] = dict()
        for key, node in zip(self.keys, self.members):
            success, result = node(input, report, index)
            if not success and node.optional:
                continue
            successes.add(success)
            results[key] = result
        if any(successes):
            return True, results
        return False, None

    def __repr__(self):
        return repr(dict(zip(self.keys, self.members)))


class ChainGroup(ChainCollection):
    NAME = 'chain-group'

    def __call__(self, input, report: Report, index=None) -> FEEDBACK[list[T2]]:
        successes: set[bool] = set()
        results: list = list()
        for node in self.members:
            success, result = node(input, report, index)
            if not success and node.optional:
                continue
            successes.add(success)
            results.append(result)
        if any(successes):
            return True, results
        return False, None

    def __repr__(self):
        return repr(list(self.members))


class ChainMatch(ChainCollection):
    NAME = "chain-match"

    def __call__(self, args: Iterable, report: Report, index=None) -> FEEDBACK[list]:
        results: list = list()
        try:
            for arg, node in zip(args, self.members, strict=True):
                success, result = node(arg, report, index)
                if not success:
                    return False, None
                results.append(result)
            return True, results
        except Exception as error:
            self.failure(args, error, report, index)
            return False, None

    def __repr__(self):
        return f"[{' | '.join(map(repr, self.members))}]"


@overload
def parse(obj: Callable[[T1], T2], **kwargs) -> ChainNode[T1, T2]: ...
@overload
def parse(obj: tuple[CHAINABLE_OBJECTS, ...], **kwargs) -> ChainSequence: ...
@overload
def parse(obj: dict[T, CHAINABLE_OBJECTS], **kwargs) -> ChainModel[T1, dict[T, T2]]: ...
@overload
def parse(obj: list[CHAINABLE_OBJECTS], **kwargs) -> ChainGroup[T1, T2]: ...


def parse(
        obj,
        **kwargs
) -> Chainable:
    raise NotImplementedError


def _parse_sequence(objs: tuple[CHAINABLE_OBJECTS, ...]) -> tuple[Chainable, ...]:
    ...
