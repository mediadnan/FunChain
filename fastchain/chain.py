"""
This module contains the implementation of Chain type,
the main object used to define data processing pipelines.

Chain can be directly imported from fastchain.
"""
import typing as tp
from ._tools import validate_name
from .chainables import Match, Sequence, Model, Group, PASS, Chainable, Node
from .factory import Factory, NodeFactory, CollectionFactory, CHAINABLES
from .monitoring import ReporterMaker, LoggingHandler, ReportDetails

T = tp.TypeVar('T')


class Chain:
    """
    Chain objects can be created and initialized at module level and used as functions,
    they are responsible for parsing the given structure into nodes and when called
    they performed the defined processing with those internal nodes.
    """
    __slots__ = '_name', '__core', '__get_reporter', '__len', 'namespace', '__required_nodes'

    def __init__(
            self,
            name: str,
            *chainables: CHAINABLES,
            log_failures: bool = True,
            namespace: str | None = None
    ) -> None:
        """Initializes a new chain with the given name and structure.

        :param name: the name that identifies the chain (should be unique).
        :param chainables: function(Any)->Any, tuple of chainables, dict str -> chainables, list of chainables ...
        :param log_failures: whether to log failures with the standard logging.Logger or not, default to True.
        :param raise_for_fail: whether to raise an exception for failures from required nodes (default None).
        :type name: str
        :type chainables: function | tuple | dict | list ...
        :type log_failures: bool
        :type raise_for_fail: bool
        """
        validate_name(name)
        core = self.parse(chainables)
        nodes = tuple(core.nodes())
        self._name: str = name
        self.namespace: str | None = namespace
        self.__required_nodes: dict[Node, bool] = {}
        self.__core: Chainable = core
        self.__len: int = len(nodes)
        handlers = []
        if log_failures:
            handlers.append(LoggingHandler)
        self.__get_reporter: ReporterMaker = ReporterMaker(name, nodes, handlers)

    @property
    def name(self) -> str:
        """gets the name of the chain - readonly"""
        if self.namespace is not None:
            return f'{self.namespace}_{self._name}'
        return self._name

    def parse(self, obj: CHAINABLES, **kwargs) -> Chainable:
        if isinstance(obj, Factory):
            title = obj.name
            if 'root' in kwargs:
                root = kwargs.pop('root')
                if 'branch' in kwargs:
                    branch = kwargs['branch']
                    root = f'{root}[{branch}]'
                title = f'{root}/{title}'
            return obj(title, **kwargs)

        elif callable(obj):
            return self.parse(NodeFactory(obj), **kwargs)

        elif isinstance(obj, tuple):
            merged = []
            options = {}
            for item in obj:
                if isinstance(item, str):
                    match item:
                        case '*':
                            options['iterable'] = True
                        case '?':
                            options['optional'] = True
                        case ':':
                            options['kind'] = Match
                        case _:
                            raise ValueError(f"unsupported option {item!r}")
                else:
                    merged.append((item, options))
                    options = {}
            del options
            if len(merged) == 1:
                return self.parse(merged[0][0], root=root, branch=branch, **kwargs, **merged[0][1])
            return self.parse(
                CollectionFactory(
                    Sequence,
                    lambda root_, **kwargs_: [
                        self.parse(obj, root=root_, branch=i, **kwargs_, **ops)
                        for i, (obj, ops) in enumerate(merged)
                    ],
                    name="pos"
                ),
                root=root,
                branch=branch,
                **kwargs
            )

        elif isinstance(obj, dict):
            return self.parse(
                CollectionFactory(
                    Model,
                    lambda root_, **kwargs_: {
                        key: self.parse(value, root=root_, branch=key, **kwargs_)
                        for key, value in obj.items()
                    }
                ),
                root=root,
                branch=branch,
                **kwargs
            )

        elif isinstance(obj, list):
            if kind is None or not issubclass(kind, (Group, Match)):
                kind = Group
            return self.parse(
                CollectionFactory(
                    kind,
                    lambda root_, **kwargs_: [
                        self.parse(obj, root=root_, branch=i, **kwargs_)
                        for i, obj in enumerate(obj)
                    ]
                ),
                root=root,
                branch=branch,
                **kwargs
            )

        elif obj is Ellipsis:
            return PASS

        else:
            raise TypeError(f"unchainable type {type(obj)}.")

    def __repr__(self) -> str:
        """representation string of the chain"""
        return f'<chain {self._name!r}>'

    def __len__(self) -> int:
        """number of nodes the chain has"""
        return self.__len

    def __call__(self, input: tp.Any, reports: dict[str, ReportDetails] | None = None):
        """
        processes the given input and returns the result,
        the chain creates its reporter and only registers it
        if reports is not None.

        :param input: the entry data to be processed
        :param reports: a dictionary where to register the execution statistics.
        :type reports: dict[str, dict[str, Any]]
        :return: the output result from given input.
        """
        reporter = self.__get_reporter()
        result = self.__core.process(input, report=reporter)[1]
        if reports is not None:
            reports[self._name] = reporter.report()
        return result


class ChainMaker:
    """Utility object for making a group of chains with the same configuration and same prefix."""
    __slots__ = 'name', 'log_failures', 'raise_for_fail', '__registered_chains__'

    def __init__(self, name: str, *, log_failures: bool = True):
        self.name: str = validate_name(name)
        self.log_failures: bool = log_failures
        self.__registered_chains__: dict[str, Chain] = {}

    def __getitem__(self, name: str) -> Chain:
        if not isinstance(name, str):
            raise TypeError("name must be str")
        try:
            return self.__registered_chains__[name]
        except KeyError:
            raise KeyError(f"no chain is registered with the name {name!r}")

    def __contains__(self, name: str) -> bool:
        return name in self.__registered_chains__

    @tp.overload
    def get(self, name: str) -> Chain | None: ...
    @tp.overload
    def get(self, name: str, default: T) -> Chain | T: ...

    def get(self, name, default=None):
        if not isinstance(name, str):
            raise TypeError("name must be a str")
        return self.__registered_chains__.get(name, default)

    def __call__(self, name: str, *chainables: CHAINABLES) -> Chain:
        """
        creates a new chain with the same configuration and same prefix.

        :param name: the name of the new chain.
        :param chainables: the body of the new chain.
        :return: the new created chain.
        """
        if name in self:
            raise ValueError("a chain with the same name already been registered.")
        new_chain = Chain(name, *chainables, log_failures=self.log_failures, namespace=self.name)
        self.__registered_chains__[name] = new_chain
        return new_chain
