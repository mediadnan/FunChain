"""
This module implements Reporter and ReporterMaker and all the tools to chain's
process monitoring and handling failed.
"""
import logging
import operator
import typing as tp
import warnings

from fastchain._abc import ReporterBase, FailureDetails, ReportDetails
from fastchain.chainables import Chainable, Node, Collection


class Reporter(ReporterBase):
    """
    Reporter object is used by the chain's internal node to report processing
    success state and errors, it is responsible for recording failed
    and produce statistics about the overall process.

    The reporter should never be created by users unless for testing purposes,
    it does no validation (intentionally) to be more optimized as it will be
    created every time the chain is called. And most of the preparation
    are taken care by the ReporterMaker.
    """
    __slots__ = 'counter', 'required_nodes', '_failures',

    def __init__(self, components: frozenset[Node], required_nodes: int) -> None:
        self.counter: dict[Node, list[bool]] = {component: [] for component in components}
        self.required_nodes: int = required_nodes
        self._failures: list[FailureDetails] = []

    def mark(self, node: Node, success: bool) -> None:
        """marks the node processing success stat"""
        try:
            self.counter[node].append(success)
        except KeyError:
            warnings.warn(
                f"unregistered node {node!r} ignored",
                UserWarning,
                stacklevel=2,
                source=self
            )

    def report_failure(self, source: Chainable, input: tp.Any, error: Exception) -> None:
        """registers the failure to be reported"""
        self._failures.append({'source': source.title, 'input': input, 'error': error, 'fatal': not source.optional})

    def report(self) -> ReportDetails:
        """builds a reporter statistics dictionary"""
        completed = 0.0
        succeeded = 0
        failed = 0
        missed = 0
        total = len(self.counter)
        for record in self.counter.values():
            record_count = len(record)
            if not record_count:
                missed += 1
                continue
            success_count = record.count(True)
            failure_count = record_count - success_count
            succeeded += success_count
            failed += failure_count
            completed += success_count / record_count
        return {
            'rate': completed / total,
            'succeeded': succeeded,
            'failed': failed,
            'missed': missed,
            'required': self.required_nodes,
            'total': total,
            'failures': self._failures
        }


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
        """prepares the new report factory with common information"""
        if not isinstance(chainable, Chainable):
            raise TypeError("chainable must be an instance of Chainable subclass")
        nodes = self.get_nodes(chainable)
        self.components: frozenset[Node] = frozenset(nodes)
        self.required_nodes: int = operator.countOf(nodes.values(), True)

    @classmethod
    def get_nodes(cls, chainable: Chainable, required: bool = True) -> dict[Node, bool]:
        """
        extracts all the chain nodes and maps them to a boolean that tells
        whether they are from an optional branch or not.
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
        """creates a new reporter with the presented information"""
        return Reporter(self.components, self.required_nodes)


class LoggingHandler:
    logger: logging.Logger
    print_stats: bool
    __slots__ = ('logger', 'print_stats')

    def __init__(self, logger: logging.Logger | str | None, print_stats: bool):
        if logger is None:
            logger = logging.getLogger('fastchain')
        elif isinstance(logger, str):
            logger = logging.getLogger(logger)
        else:
            if not isinstance(logger, logging.Logger):
                raise TypeError(f'logger must be an instance of {logging.Logger}')
        self.logger = logger
        self.print_stats = print_stats

    def _handle_failure(self, failure: FailureDetails) -> None:
        source, input, error = failure['source'], failure['input'], failure['error']
        level = logging.ERROR if failure['fatal'] else logging.INFO
        message = f"{source} raised {error!r} when receiving {type(input)!r}: {input!r}"
        self.logger.log(level, message)

    def _handle_stats(self, report: ReportDetails) -> None:
        if not self.print_stats:
            return
        print("-- STATS -----------------------------",
              f"\tsuccess percentage:        {round(report['rate'] * 100)}%",
              f"\tsuccessful operations:     {report['succeeded']}",
              f"\tunsuccessful operations:   {report['failed']}",
              f"\tunreached nodes:           {report['missed']}",
              f"\trequired nodes:            {report['required']}",
              f"\ttotal number of nodes:     {report['total']}",
              "--------------------------------------",
              sep='\n')

    def handle_report(self, report: ReportDetails) -> None:
        self._handle_stats(report)
        for failure in report['failures']:
            self._handle_failure(failure)
