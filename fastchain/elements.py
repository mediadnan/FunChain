from logging import Logger
from abc import ABC, abstractmethod
from functools import reduce
from typing import (
    Optional,
    Tuple,
    Any,
    Dict,
    Set,
    Iterable,
)

from .wrapper import Wrapper
from .reporter import Reporter
from .tools import validate


#   ABSTRACT BASE CLASSES ------------------------------------------------
class ChainableNode(ABC):
    __doc__ = """
        chainables or chainable nodes are callable objects that can be chained together,
        chained nodes are executed in sequence one passing it result to the next until the last one.

        calling a chainable returns a tuple of success_indicator and result, the indicator informs
        specifically root chainables if the sub chainables have succeeded or not.

        if one chained node fails, the execution halts and returns the default.
    """

    __branch: str
    __title: str

    __root: Optional['ChainCollection'] = None
    __next: Optional['ChainableNode'] = None
    __prev: Optional['ChainableNode'] = None

    # Construction  ------------------------------------------------------

    def __init__(self, branch: str, title: str) -> None:
        self.__branch = branch
        self.__title = title

    # Identity  ----------------------------------------------------------

    @property
    def branch(self):
        """gets the branch name - read-only"""
        return self.__branch

    @property
    def title(self) -> str:
        """name of the component - read-only"""
        return self.__title

    @property
    def position(self) -> Tuple[int, ...]:
        """absolute position preceded by the subgroups' - read-only"""
        return *(self.__root.position if self.__root else ()), len(self.previous_all)

    @property
    def default(self) -> Any:
        """the value to be returned when failing - read-only"""
        return None

    @property
    def size(self) -> int:
        """size without counting next - read-only"""
        return 1

    def __str__(self) -> str:
        """unique composition of [namespace] :: [title] [position]"""
        return f"{self.__branch} :: {self.title} {self.position}"

    def __len__(self) -> int:
        if self.next is None:
            return self.size
        return self.size + len(self.next)

    # Navigation  --------------------------------------------------------

    def chain(self, other: 'ChainableNode') -> 'ChainableNode':
        """binds the chainable (as next) and returns it"""
        other.previous = self
        self.__next = other
        return other

    @property
    def root(self) -> Optional['ChainCollection']:
        """gets the root of this component"""
        return self.__root

    @root.setter
    def root(self, other: 'ChainCollection') -> None:
        self.__root = validate(other, 'root', ChainCollection)

    @property
    def next(self) -> Optional['ChainableNode']:
        """gets the successor of this component - read-only"""
        return self.__next

    @property
    def previous(self) -> Optional['ChainableNode']:
        """gets the predecessor of this component"""
        return self.__prev

    @previous.setter
    def previous(self, other: 'ChainableNode') -> None:
        self.__prev = validate(other, 'previous', ChainableNode)

    @property
    def roots(self) -> Tuple['ChainCollection', ...]:
        """gets all roots of this component - read-only"""
        if not self.root:
            return ()
        return *self.root.roots, self.root

    @property
    def next_all(self) -> Tuple['ChainableNode', ...]:
        """gets all successors of this component - read-only"""
        if not self.next:
            return ()
        return self.next, *self.next.next_all

    @property
    def previous_all(self) -> Tuple['ChainableNode', ...]:
        """gets all predecessors of this component - read-only"""
        if not self.previous:
            return ()
        return *self.previous.previous_all, self.previous

    @property
    def origin(self) -> Optional['ChainCollection']:
        """gets the first root of this component - read-only"""
        if not self.root:
            return self if isinstance(self, ChainCollection) else None
        return self.root.origin

    @property
    def last(self) -> 'ChainableNode':
        """gets the first component of the sequence - read-only"""
        if not self.next:
            return self
        return self.next.last

    @property
    def first(self):
        """gets the first component of the sequence - read-only"""
        if not self.previous:
            return self
        return self.previous.first

    @property
    def sequence(self) -> Tuple['ChainableNode', ...]:
        """gets all chained components from first to last - read-only"""
        return *self.previous_all, self, *self.next_all

    # Reporting  ---------------------------------------------------------

    def report_success(self, reporter: Optional[Reporter]) -> None:
        """reports a successful operation"""
        if reporter:
            reporter.success(self)

    def report_failure(
            self,
            reporter: Optional[Reporter],
            logger: Optional[Logger],
            input,
            error,
            **kwargs
    ) -> None:
        """reports a failed operation"""
        if reporter:
            reporter.failure(
                self,
                dict(
                    input=input,
                    output=self.default,
                    error=error,
                    root=repr(self.root),
                    previous=repr(self.previous),
                    **kwargs
                )
            )
        if logger:
            logger.error(f"{input!r} -> {self!r} !! {error!r} -> {self.default!r}")

    # Functionality  -----------------------------------------------------

    @abstractmethod
    def _context(self, arg, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        """uses arg and returns the result_state and the result"""

    def _call_next(self, result: Any, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        """calls the next node with the result"""
        return self.next(result, reporter, log)  # type: ignore

    def __call__(self, arg: Any, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        """takes an input value and returns the success indicator and the result or default"""
        state, result = self._context(arg, reporter, log)
        if not state or self.__next is None:
            return state, result
        return self._call_next(result, reporter, log)


class ChainCollection(ChainableNode, ABC):
    __doc__ = """chain collection are nodes that have children or sub-nodes that do the actual job"""

    __members: Set[ChainableNode]

    def __init__(self, branch: str) -> None:
        super().__init__(branch, type(self).__name__)
        self.__members = set()

    def own(self, other: ChainableNode) -> ChainableNode:
        """makes self as root of other and keeps it references as member"""
        self.__members.add(other)
        other.root = self
        return other

    @property
    def members(self) -> Set[ChainableNode]:
        """gets all children elements - read-only"""
        return self.__members


class ChainOption(ChainableNode, ABC):
    __doc__ = """chain options are helper nodes that affect chain behaviour without changing the passed argument"""

    _option_: str

    def __init__(self, branch: str) -> None:
        super().__init__(branch, f'OPTION[{self._option_}]')

    def __repr__(self) -> str:
        return self._option_


#   CHAIN OPTIONS   ------------------------------------------------------
class ChainMapOption(ChainOption):
    __doc__ = """chain map option takes an iterable and pass each value to the next node."""

    _option_ = '*'

    @property
    def default(self) -> tuple:
        return ()

    def _context(self, args: Iterable, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        try:
            iter(args)
        except TypeError as type_error:
            self.report_failure(reporter, log, args, type_error)
            return False, self.default
        self.report_success(reporter)
        return True, args

    def _call_next(self, results: Iterable, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        flags, results = zip(*(self.next(result, reporter, log) for result in results))  # type: ignore
        return all(flags), results


#   CHAIN FUNCTION  ------------------------------------------------------
class ChainFunc(ChainableNode):
    __doc__ = """
    chain functions are the main chainable nodes, the only chainable that actually change a value and pass it
    to the next node, the object is a wrapper around a wrapper (Wrapper object) that wraps some function.

    chain function object runs the wrapped function inside a safe try...except context, if the execution
    of the function returns a value then it marks a success and passes the result to next,
    but if it raises some exception, it marks it as a failure with all details and returns a default value
    without calling next.
    """

    _func: Wrapper

    def __init__(self, func: Wrapper, branch: str):
        super().__init__(branch, func.name)
        self._func = func

    @property
    def default(self) -> Any:
        return self._func.default

    def __repr__(self) -> str:
        return f'[{self._func!r}]'

    def _context(self, arg, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        try:
            result = self._func.function(arg)
        except Exception as err:
            self.report_failure(reporter, log, arg, err)
            return False, self.default
        self.report_success(reporter)
        return True, result


#   CHAIN COLLECTIONS   --------------------------------------------------
class ChainGroup(ChainCollection):
    __doc__ = """
    chain groups are containers that chain nodes together and hold reference of the first element named entry,
    calling a chain group will call it entry node and it next nodes internally then pass the result to group's next.
    the chain will return a success_indicator and a result.

    the chain group indicates failure if ANY of it members fail.

    it is the choice for making sequential operations.

    the groups owns the members, each of the sub-nodes keeps reference of this group as root.
    """

    __entry: ChainableNode

    def __init__(self, members: Tuple[ChainableNode, ...], branch: str) -> None:
        if not members:
            raise ValueError('chain groups must contain elements')
        super().__init__(branch)
        self.__entry = reduce(ChainableNode.chain, (self.own(member) for member in members)).first

    @property
    def entry(self) -> ChainableNode:
        """gets the first member of the subsequence - read-only"""
        return self.__entry

    @property
    def default(self) -> None:
        return None

    @property
    def size(self) -> int:
        return len(self.entry)

    def __repr__(self) -> str:
        return f"({' => '.join(map(repr, self.entry.sequence))})"

    def __getitem__(self, item: int) -> ChainableNode:
        sequence = self.entry.sequence
        try:
            return sequence[item]
        except IndexError:
            raise IndexError(f"index out of range, last index is {len(sequence) - 1}") from None

    def _context(self, arg, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        return self.entry(arg, reporter, log)


class ChainModel(ChainCollection):
    __doc__ = """
    chain models are containers that map branch_names to nodes, calling a model
    will call each member with the given argument and return a success_indicator
    and a dictionary mapping branch_names to results.

    the chain model indicates failure when ALL of it members fail.

    it is the choice for making 'parallel' operations.

    the groups owns the members, each of the sub-nodes keeps reference of this group as root.
    """

    __model: Dict[str, ChainableNode]

    def __init__(self, members: Dict[str, ChainableNode], branch: str) -> None:
        super().__init__(branch)
        if not members:
            raise ValueError('chain models must contain elements')
        self.__model = {name: self.own(component) for name, component in members.items()}

    @property
    def model(self) -> Dict[str, ChainableNode]:
        """gets the model dictionary - read-only"""
        return self.__model

    @property
    def default(self) -> Any:
        return dict()

    @property
    def size(self) -> int:
        return sum(map(len, self.model.values()))

    def __repr__(self) -> str:
        return repr(self.model)

    def __getitem__(self, item: str) -> ChainableNode:
        try:
            return self.model[item]
        except KeyError:
            raise KeyError(f'chain model has no key named {item}')

    def _context(self, arg, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        states = set()
        results = dict()
        for name, component in self.model.items():
            state, result = component(arg, reporter, log)
            states.add(state)
            results[name] = result
        return any(states), results
