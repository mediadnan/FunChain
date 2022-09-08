import abc
from functools import partial, partialmethod
from itertools import chain
from types import NoneType
from typing import Any, Generator, TypeVar, Iterable, Callable

from .monitoring import Reporter


T = TypeVar('T')


# +-+ Abstract base classes +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
class Node(abc.ABC):
    """Base class for all chain nodes"""
    __slots__ = 'name', 'title', 'core', 'optional'

    core: T
    name: str
    title: str
    optional: bool

    def __init__(self, core: T, name: str) -> None:
        if not isinstance(name, str):
            raise TypeError(f"The {self.__class__.__name__} name must be str")
        self.name = name
        self.title = name
        self.core = core
        self.optional = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}'>"

    @abc.abstractmethod
    def __call__(self, input, reporter: Reporter) -> tuple[bool, Any]:
        """Processes the input and returns the success state and result"""

    @property
    @abc.abstractmethod
    def expose(self) -> dict['Node', bool]:
        """Exposes all the functions and whether they are required"""

    def default(self) -> Any:
        """The value to be returned in case of failure"""
        return None

    def failure(self, input, error: Exception, reporter: Reporter) -> None:
        """Consistent way for nodes to report failures"""
        reporter.failure(self.title, input, error, not self.optional)

    def set_title(self, root: str | None = None, branch: Any = None, /) -> None:
        """Sets the node title from a root and branch"""
        if root is None:
            self.title = self.name
            return
        if branch is not None:
            root = f'{root}[{branch}]'
        self.title = f'{root}.{self.name}'


class NodeGroup(Node, abc.ABC):
    """Base class for all node groups"""
    default_name: str

    def __init__(self, nodes, name: str | None = None):
        if name is None:
            name = self.default_name
        super(NodeGroup, self).__init__(nodes, name)

    @property
    @abc.abstractmethod
    def nodes(self) -> Generator[Node, None, None]:
        """Returns an iterable of the node members"""

    @property
    @abc.abstractmethod
    def branches(self) -> Generator[tuple[Any, Node], None, None]:
        """Returns an iterable of tuples with keys and node members"""

    @property
    def expose(self) -> dict[Node, bool]:
        """Returns a dict mapping chainables to whether they're required"""
        return {node: (required and not self.optional)
                for node, required in
                chain(*(node.expose.items() for node in self.nodes))}

    def set_title(self, root: str | None = None, branch: Any = None, /) -> None:
        """Sets the group's and group's node titles from root and branch"""
        super(NodeGroup, self).set_title(root, branch)
        for key, node in self.branches:
            node.set_title(self.title, key)


class NodeSequence(NodeGroup, abc.ABC):
    """Base class for all node groups with a list of nodes"""
    core: list[Node]

    def __init__(self, nodes: list[Node], name: str | None = None):
        if not (isinstance(nodes, list) and all(isinstance(node, Node) for node in nodes)):
            raise TypeError(f"{type(self).__name__} nodes must be a list of {Node} objects")
        elif not nodes:
            raise ValueError(f"Cannot create an empty {type(self).__name__}")
        super().__init__(nodes, name)

    @property
    def nodes(self) -> Generator[Node, None, None]:
        yield from self.core

    @property
    def branches(self) -> Generator[tuple[Any, Node], None, None]:
        yield from enumerate(self.core)


class NodeMapping(NodeGroup, abc.ABC):
    """Base class for all node groups with a dict of nodes"""
    core: dict[Any, Node]

    def __init__(self, nodes: dict[Any, Node], name: str | None = None):
        if not (isinstance(nodes, dict) and all(isinstance(node, Node) for node in nodes.values())):
            raise TypeError(f"{type(self).__name__} nodes must be a dict mapping keys to {Node} objects")
        elif not nodes:
            raise ValueError(f"Cannot create an empty {type(self).__name__}")
        super().__init__(nodes, name)

    @property
    def nodes(self) -> Generator[Node, None, None]:
        yield from self.core.values()

    @property
    def branches(self) -> Generator[tuple[Any, Node], None, None]:
        yield from self.core.items()


class NodeWrapper(Node, abc.ABC):
    """Base class for all the node wrappers"""
    core: Node

    def __init__(self, core: Node) -> None:
        if not isinstance(core, Node):
            raise TypeError(f"{self.__class__.__name__} only wraps {Node} instances")
        super().__init__(core, core.name)

    def failure(self, input, error: Exception, reporter: Reporter) -> None:
        self.core.failure(input, error, reporter)

    def default(self) -> Any:
        return self.core.default()

    @property
    def expose(self) -> dict[Node, bool]:
        return self.core.expose

    def set_title(self, root: str | None = None, branch: Any = None, /) -> None:
        super(NodeWrapper, self).set_title(root, branch)
        self.core.set_title(root, branch)


# +-+ Nodes section +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
class Chainable(Node):
    """The main leaf node that wraps a function"""
    core: Callable[[Any], Any]

    def __init__(self, function: Callable[[Any], Any], name: str | None = None) -> None:
        if name is None:
            name = self.qualname(function)
        if not callable(function):
            raise TypeError("The chainable function must be callable")
        super(Chainable, self).__init__(function, name)

    def __call__(self, input, reporter: Reporter) -> tuple[bool, Any]:
        """Executes the function inside a safe block and reports the execution info"""
        try:
            result = self.core(input)
        except Exception as error:
            reporter.mark(self, False)
            self.failure(input, error, reporter)
            return False, self.default()
        reporter.mark(self, True)
        return True, result

    @classmethod
    def qualname(cls, function) -> str:
        """Gets the function's __qualname__"""
        if isinstance(function, (partial, partialmethod)):
            return cls.qualname(function.func)
        elif hasattr(function, '__qualname__'):
            return function.__qualname__
        return type(function).__qualname__

    @property
    def expose(self) -> dict[Node, bool]:
        return {self: not self.optional}


class Pass(Node):
    """The passive node that does nothing but returning the same input"""
    core: NoneType

    def __init__(self) -> None:
        """Only needs to be initialized once"""
        super(Pass, self).__init__(None, 'pass')

    def __call__(self, input, reporter: Reporter) -> tuple[bool, Any]:
        """Forwards the same input with a success state"""
        return True, input

    @property
    def expose(self) -> dict[Node, bool]:
        """Returns an empty dict"""
        return {}

    def set_title(self, root: str | None = None, branch: Any = None, /) -> None:
        """Pass ignores title setting"""


# +-+ Node groups section +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
class Sequence(NodeSequence):
    """The group of nodes that will be chained sequentially"""
    default_name = 'sequence'

    def __init__(self, nodes: list[Node], name: str | None = None) -> None:
        """Initializes and validates the sequence"""
        super(Sequence, self).__init__(nodes, name)
        if all((node.optional for node in nodes)):
            raise ValueError("At least one node must be required, or make the whole Sequence optional")

    def __call__(self, input, reporter: Reporter) -> tuple[bool, Any]:
        """Executes the nodes by piping results until the last one"""
        for node in self.nodes:
            success, result = node(input, reporter)
            if success:
                input = result
            elif not node.optional:
                return False, result
        return True, input


class ListModel(NodeSequence):
    """The list of nodes that returns a list of results"""
    default_name = 'model'

    def __call__(self, input, reporter: Reporter) -> tuple[bool, list]:
        """Executes each node branch and returns the result with the same structure"""
        success = True
        results = []
        for node in self.nodes:
            success_, result = node(input, reporter)
            if not success_:
                if node.optional:
                    continue
                success = False
            results.append(result)
        return success, results

    def default(self) -> list:
        """Returns a list of required nodes' defaults"""
        return [node.default() for node in self.nodes if not node.optional]


class DictModel(NodeMapping):
    """The dict of nodes that returns a dict of results"""
    default_name = 'model'

    def __call__(self, input, reporter: Reporter) -> tuple[bool, dict]:
        """Executes each node branch and returns the result with the same structure"""
        success = True
        results = {}
        for key, node in self.branches:
            success_, result = node(input, reporter)
            if not success_:
                if node.optional:
                    continue
                success = False
            results[key] = result
        return success, results

    def default(self) -> dict:
        """Returns a dict of required nodes' defaults"""
        return {key: node.default() for key, node in self.branches if not node.optional}


class Match(NodeSequence):
    """The node that passes each item of an iterable input to the corresponding branch"""
    default_name = 'match'

    def __init__(self, nodes: list[Node], name: str | None = None):
        """Initializes and validates the match nodes"""
        super().__init__(nodes, name)
        if len(nodes) < 2:
            raise ValueError("The Match should at least contain two branches")

    def __call__(self, inputs: Iterable, reporter: Reporter) -> tuple[bool, list]:
        """Executes each node branch with a corresponding input"""
        success = True
        results = []
        try:
            for input, node in zip(inputs, self.nodes, strict=True):
                success_, result = node(input, reporter)
                if not success_:
                    success = False
                results.append(result)

        # May fail for non-iterable input or different iterable sizes
        except Exception as error:
            self.failure(inputs, error, reporter)
            return False, self.default()
        return success, results

    def default(self) -> list:
        return [member.default() for member in self.nodes]


# +-+ Node options section +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
class Loop(NodeWrapper):
    """Wraps a node and executes it for each item of an iterable input"""
    def __call__(self, inputs: Iterable, reporter: Reporter) -> tuple[bool, Generator]:
        """Executes the node for each item of the inputs"""
        try:
            return True, (result for success, result in (self.core(input, reporter) for input in inputs) if success)
        except Exception as error:
            self.failure(inputs, error, reporter)
            return False, self.default()

    def default(self) -> Generator:
        """Returns an empty generator"""
        yield from ()
