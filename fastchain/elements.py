import abc
from abc import ABC, abstractmethod
from typing import Any, TypeAlias, TypeVar, Iterable, Generic, Callable, Generator, overload, TYPE_CHECKING

from .reporter import Reporter
from ._tools import get_qualname

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
FEEDBACK: TypeAlias = tuple[True, T] | tuple[False, Any]
CHAINABLE: TypeAlias = Callable[[T1], T2]
CHAINABLE_OBJECTS: TypeAlias = CHAINABLE | tuple | dict[str | int, Any] | list | str


class ChainFailure(Exception):
    """special Exception that signals a failing operation"""


class Chainable(ABC, Generic[T1, T2]):
    __slots__ = (
        'name',
        'title',
        'optional',
        'default'
    )

    def __init__(
            self,
            name: str,
            *,
            title: str | None = None,
            root: str | None = None,
            pos: int | None = None,
            optional: bool = False,
            default: Any = None,
    ):
        if title is None:
            title = name
            if pos is not None:
                title = f'{title}[{pos}]'
            if root is not None:
                title = f'{root}.{title}'
        self.title: str = title
        self.name: str = name
        self.optional: bool = optional
        self.default: T2 | None = default

    def __str__(self):
        return self.title

    @abc.abstractmethod
    def __repr__(self) -> str:
        """chainable string representation"""

    @abstractmethod
    def __call__(self, arg: T1, reporter: Reporter) -> FEEDBACK[T2]:
        """processes arg and returns feedback with success and result"""

    def failure(self, reporter: Reporter, input: Any, error: Exception) -> tuple[False, Any]:
        """reports self as failed with given input and error"""
        reporter.failed(self, input=input, error=error, ignore=self.optional)
        return False, self.default


class ChainNode(Chainable, Generic[T1, T2]):
    __slots__ = 'function',

    def __init__(self, function: Callable[[T1], T2], **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = get_qualname(function)
        self.function: CHAINABLE[T1, T2] = function
        super().__init__(**kwargs)

    def __call__(self, arg: T1, reporter: Reporter) -> FEEDBACK[T2]:
        try:
            result = self.function(arg)
        except Exception as err:
            self.failure(reporter, arg, err)
            return False, self.default
        reporter.success(self)
        return True, result

    def __repr__(self) -> str:
        return f'<{self.name}>'


class ChainMap(Chainable):
    __slots__ = 'node',

    def __init__(self, node: Chainable[T1, T2]):
        super(ChainMap, self).__init__(title=node.title, name=node.name, optional=node.optional, default=())
        self.node: Chainable = node

    def __repr__(self):
        return f'*{self.node!r}'

    def __call__(self, args: Iterable[T1], reporter: Reporter) -> FEEDBACK[Iterable[T2]]:
        try:
            iter(args)
        except TypeError as error:
            return self.failure(reporter, args, error)
        return True, self._process(args, reporter)

    def _process(self, args: Iterable[T1], reporter: Reporter) -> Generator[T2, None, None]:
        for arg in args:
            success, result = self.node(arg, reporter)
            if success:
                yield result
            elif self.optional:
                continue
            break


class ChainCollection(Chainable, ABC):
    __slots__ = 'nodes',
    NAME: str = 'chain-collection'

    def __init__(self, nodes: Iterable[Chainable], **kwargs):
        self.nodes: tuple[Chainable, ...] = tuple(nodes)
        if 'name' not in kwargs:
            kwargs['name'] = self.NAME
        if 'optional' not in kwargs:
            kwargs['optional'] = all(node.optional for node in nodes)
        super(ChainCollection, self).__init__(**kwargs)


class ChainSequence(ChainCollection, Generic[T1, T2]):
    NAME = 'chain-sequence'

    def __init__(self, nodes: tuple[Chainable[T1, Any], ..., Chainable[Any, T2]], **kwargs):
        for node in reversed(nodes):
            if not node.optional:
                kwargs['default'] = node.default
                break
        super(ChainSequence, self).__init__(nodes, **kwargs)

    def __call__(self, arg: T1, reporter: Reporter) -> FEEDBACK[T2]:
        for node in self.nodes:
            success, result = node(arg, reporter)
            if success:
                arg = result
                continue
            elif not node.optional:
                break
        else:
            return False, self.default
        return success, result

    def __repr__(self):
        return ' -> '.join(map(repr, self.nodes))


class ChainModel(ChainCollection):
    NAME = 'chain-model'
    __slots__ = 'keys',

    def __init__(self, model: dict[T, Chainable], **kwargs):
        kwargs['default'] = {key: node.default for key, node in model.items() if not node.optional}
        self.keys, nodes = zip(*model.items())
        super().__init__(nodes, **kwargs)

    def __call__(self, arg: T1, reporter: Reporter) -> FEEDBACK[dict[T, T2]]:
        result = {}
        for key, node in zip(self.keys, self.nodes):
            success, result = node(arg, reporter)
            if success:
                result[key] = result
            elif not node.optional:
                return False, self.default | result
        return True, result

    def __repr__(self):
        return repr(dict(zip(self.keys, self.nodes)))


class ChainGroup(ChainCollection):
    NAME = 'chain-group'

    def __init__(self, nodes: list[Chainable], **kwargs):
        kwargs['default'] = []
        super().__init__(nodes, **kwargs)

    def __call__(self, arg: T1, reporter: Reporter) -> FEEDBACK[list[T2]]:
        results = []
        for node in self.nodes:
            success, result = node(arg, reporter)
            if success:
                results.append(result)
            elif not node.optional:
                return False, self.default
        return True, results

    def __repr__(self):
        return repr(list(self.nodes))


class ChainMatch(ChainCollection):
    NAME = "chain-match"

    def __init__(self, nodes: list[Chainable], **kwargs):
        kwargs['default'] = (node.default for node in nodes if not node.optional)
        super().__init__(nodes, **kwargs)

    def __call__(self, args: Iterable[T1], reporter: Reporter) -> FEEDBACK[list[T2]]:
        results = []
        try:
            for arg, node in zip(args, self.nodes, strict=True):
                success, result = node(arg, reporter)
                if success:
                    results.append(result)
                elif not node.optional:
                    return False, self.default
            return True, results
        except TypeError as error:
            return self.failure(reporter, args, error)

    def __repr__(self):
        return f"[{' | '.join(map(repr, self.nodes))}]"


@overload
def parse(obj: Callable[[T1], T2], **kwargs) -> ChainNode[T1, T2]: ...
@overload
def parse(obj: tuple[CHAINABLE_OBJECTS, ...], **kwargs) -> ChainSequence: ...
@overload
def parse(obj: dict[T, CHAINABLE_OBJECTS], **kwargs) -> ChainModel[T1, dict[T, T2]]: ...
@overload
def parse(obj: list[CHAINABLE_OBJECTS], **kwargs) -> ChainGroup[T1, T2]: ...


def parse(obj, **kwargs) -> Chainable: ...
