"""
This module implements Reporter and ReporterMaker and all the tools to chain's
process monitoring and handling failures.
"""
import operator
import warnings
import typing as tp

from fastchain._abc import ReporterBase, FailureDetails, ReportStatistics
from fastchain.chainables import Chainable, Node, Collection


class FakeReporter(ReporterBase):
    """Reporter that does nothing when called"""
    def __init__(self):
        self.failures = []

    def __call__(self, component, success: bool) -> None:
        pass

    def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None:
        pass

    def statistics(self) -> ReportStatistics:
        return ReportStatistics()


class Reporter(ReporterBase):
    """
    Reporter object is used by the chain's internal component to report processing
    success state and errors, it is responsible for recording failures
    and produce statistics about the overall process.

    The reporter should never be created by users unless for testing purposes,
    it does no validation (intentionally) to be more optimized as it will be
    created every time the chain is called. And most of the preparation
    are taken care by the ReporterMaker.
    """
    __slots__ = 'counter', 'required_nodes', 'failures',

    def __init__(self, components: frozenset[Node], required_nodes: int) -> None:
        self.counter: dict[Node, list[bool]] = {component: [] for component in components}
        self.required_nodes: int = required_nodes
        self.failures: list[FailureDetails] = []

    def __call__(self, node: Node, success: bool) -> None:
        """
        marks success state of a previously registered node

        :param node: registered node
        :type node: Node
        :param success: True if operation succeeded or False otherwise
        :type success: bool
        :return: None
        """
        try:
            self.counter[node].append(success)
        except KeyError:
            warnings.warn(
                f"unregistered node {node!r} ignored",
                UserWarning,
                stacklevel=2,
                source=self
            )

    def register_failure(
            self,
            source: str,
            input: tp.Any,
            error: Exception,
            fatal: bool = False
    ) -> None:
        """
        registers the failure to be reported.

        :param source: the coll_title of the reporter object.
        :param input: the value that caused the failure.
        :param error: the risen exception.
        :param fatal: True if the error is from a required node
        """
        self.failures.append(dict(source=source, input=input, error=error, fatal=fatal))

    def statistics(self) -> ReportStatistics:
        """
        builds a reporter statistics dictionary with the following information;

        **success_rate** *(float)*
            ratio (between 0.0 - 1.0) of registered node successes over total number of nodes

        **minimum_expected_rate** *(float)*
            ratio (between 0.0 - 1.0) of required nodes over total number of nodes

        **successful_node_operations** *(int)*
            number of reported successful operations from the same or different nodes

        **failed_node_operations** *(int)*
            number of reported failing operations from the same or different nodes

        **missed_nodes** *(int)*
            number of unreached chain nodes

        **total_nodes** *(int)*
            total number of the chain's node

        :return: dictionary of success_rate, minimum_expected_rate, successful_node_operations,
                 failed_node_operations, missed_nodes and total_nodes
        :rtype: dict
        """
        completed = 0.0
        successes = 0
        failures = 0
        misses = 0
        total = len(self.counter)
        for record in self.counter.values():
            record_count = len(record)
            if not record_count:
                misses += 1
                continue
            success_count = record.count(True)
            failure_count = record_count - success_count
            successes += success_count
            failures += failure_count
            completed += success_count / record_count
        return dict(
            success_rate=round(completed / total, 4),
            minimum_expected_rate=self.required_nodes,
            successful_node_operations=successes,
            failed_node_operations=failures,
            missed_nodes=misses,
            total_nodes=total,
        )


class ReporterMaker:
    """
    ReporterMaker object is a reporter factory used by the chain to prepare
    some initial state related to the chain itself and not to its processing input
    to minimize the impact of creating reports for each call.

    This layer has been added to separate thing that should be executed once (when
    defining the chain) and things that will be executed each time the chain is triggered.

    ReporterMaker is not expected to be created by users (unless for testing),
    the full process is abstracted away and should be taken care of by the chain's constructor.
    """
    __slots__ = 'components', 'required_nodes', 'failure_handlers',

    def __init__(self, chainable: Chainable) -> None:
        """
        Initializes new ReporterMaker object with the given information.

        :param chainable: chainables that will be reporting.
        :type chainable: Iterable[Chainable]
        """
        if not isinstance(chainable, Chainable):
            raise TypeError("chainable must be an instance of Chainable subclass")
        nodes = self.get_nodes(chainable)
        self.components: frozenset[Node] = frozenset(nodes)
        self.required_nodes: int = operator.countOf(nodes.values(), True)

    @classmethod
    def get_nodes(cls, chainable: Chainable, required: bool = True) -> dict[Node, bool]:
        """
        extracts all the chain nodes and determine if they are required or optional
        depending on their roots, they are considered required if neither
        they nor their parents are optional.

        :param chainable: Chainable subclass instance.
        :type chainable: Node | Collection
        :param required: holds previous required state when recusing
        :type required: bool
        :return: dict mapping nodes to their required state.
        :rtype: dict[Node, bool]
        """
        required = required and not chainable.optional
        nodes: dict[Node, bool] = dict()
        if isinstance(chainable, Collection):
            for member in chainable.members:
                nodes.update(cls.get_nodes(member, required))
        elif isinstance(chainable, Node):
            nodes[chainable] = required
        return nodes

    def __call__(self) -> Reporter:
        """creates a new Reporter object with the previously specified information."""
        return Reporter(self.components, self.required_nodes)
