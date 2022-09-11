"""
This module implements Reporter and ReporterMaker and all the tools to chain's
process monitoring and handling failed.
"""

from typing import Any, Callable, TypedDict, TypeAlias
from logging import INFO, ERROR, getLogger


class Failure(TypedDict):
    source: str
    input: Any
    error: Exception
    fatal: bool


class Report(TypedDict):
    rate: float
    succeeded: int
    failed: int
    missed: int
    required: int
    total: int
    failures: list[Failure]


ReportHandler: TypeAlias = Callable[[Report], None]


class Reporter:
    __slots__ = 'failures', 'counter'
    FailureKeys: tuple[str, str, str, str] = 'source', 'input', 'error', 'fatal'

    def __init__(self) -> None:
        self.failures: list[tuple[str, Any, Exception, bool]] = list()
        self.counter: dict[Any, list[int]] = dict()

    def mark(self, node: Any, success: bool) -> None:
        if node not in self.counter:
            self.counter[node] = [0, 0]
        self.counter[node][success] += 1

    def failure(self, source: str, input, error: Exception, fatal: bool) -> None:
        self.failures.append((source, input, error, fatal))

    def report(self, nodes: frozenset[Any] | None = None, required: int | None = None) -> Report:
        """builds a reporter statistics dictionary"""
        completed = 0
        succeeded = 0
        failed = 0
        for record in self.counter.values():
            failure_count, success_count = record
            succeeded += success_count
            failed += failure_count
            completed += success_count / (success_count + failure_count)
        if nodes is None:
            total = len(self.counter) or 1
            required = total
            missed = 0
        else:
            total = len(nodes) or 1
            required = required if required is not None else total
            missed = len(nodes.difference(self.counter))
        return {
            'rate': completed / total,
            'succeeded': succeeded,
            'failed': failed,
            'missed': missed,
            'required': required,
            'total': total,
            'failures': [dict(zip(self.FailureKeys, failure)) for failure in self.failures]
        }


def print_report(report: Report) -> None:
    """prints report metrics using print()"""
    print("-- STATS -----------------------------",
          f"   success percentage:        {report['rate']:.0%}",
          f"   successful operations:     {report['succeeded']}",
          f"   unsuccessful operations:   {report['failed']}",
          f"   unreached nodes:           {report['missed']}",
          f"   required nodes:            {report['required']}",
          f"   total number of nodes:     {report['total']}",
          "--------------------------------------",
          sep='\n')


def failures_logger(logger: str | None) -> Callable[[Report], None]:
    """
    Generates a function that logs failures from a report

    :param logger: The logger used to log failures, retrieved by logging.getLogger(logger)
    """
    def log_failures(report: Report) -> None:
        """logs the reported failures"""
        for failure in report['failures']:
            level = ERROR if failure['fatal'] else INFO
            source, input, error = failure['source'], failure['input'], failure['error']
            message = f"{source} raised {error!r} when receiving {type(input).__name__}: {input!r}"
            _logger.log(level, message)
    _logger = getLogger(logger)
    return log_failures
