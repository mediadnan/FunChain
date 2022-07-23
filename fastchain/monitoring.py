import abc
import warnings
from logging import Logger, INFO, ERROR, getLogger
from typing import TypedDict, TypeVar, Generic, Iterable, Any, Callable


T = TypeVar('T')


class FailureDetails(TypedDict):
    """standard failure details dictionary"""
    source: str
    input: Any
    error: Exception
    fatal: bool


class ReportDetails(TypedDict):
    """standard report details dictionary"""
    rate: float
    expected_rate: float
    succeeded: int
    missed: int
    failed: int
    total: int
    failures: list[FailureDetails]


class ChainFailure(RuntimeError):
    """custom exception optionally raised by a chain in case of failure"""


class FailureHandler(abc.ABC):
    __slots__ = 'owner',

    def __init__(self, owner: str):
        if not owner:
            raise ValueError(f"cannot create a {self.name} without owners name")
        self.owner = owner

    @staticmethod
    def message(failure: FailureDetails) -> str:
        source, input, error = failure['source'], failure['input'], failure['error']
        return f"{source!r} raised {error!r} after receiving {input!r} (type: {type(input)})"

    @abc.abstractmethod
    def __call__(self, failure: FailureDetails) -> None: pass
    @property
    @abc.abstractmethod
    def name(self) -> str: pass


class LoggingHandler(FailureHandler):
    name: str = "logging handler"

    def __init__(self, owner: str):
        super(LoggingHandler, self).__init__(owner)
        self.logger: Logger = getLogger(owner)

    def __call__(self, failure: FailureDetails):
        self.logger.log(ERROR if failure['fatal'] else INFO, self.message(failure), stacklevel=2)


class RaiseFailureHandler(FailureHandler):
    name: str = "raise_for_failures handler"

    def __call__(self, failure: FailureDetails) -> None:
        if failure['fatal']:
            raise ChainFailure(f"{self.owner} :: {self.message(failure)}")


class Report(Generic[T]):
    __slots__ = 'counter', 'required', 'failures', 'failure_handlers',

    def __init__(self, components: frozenset[T], required: int, failure_handlers: list[FailureHandler]):
        self.counter: dict[T, list[bool]] = {component: [] for component in components}
        self.required: int = required
        self.failures: list[FailureDetails] = []
        self.failure_handlers: list[FailureHandler] = failure_handlers

    def __call__(self, component: T, success: bool) -> None:
        """
        marks the registered component result as success or failure for statistics.

        :param component: one of the previously registered components.
        :param success: either True for successful operations or False for unsuccessful ones.
        :return: None
        """
        try:
            self.counter[component].append(success)
        except KeyError:
            warnings.warn(
                f"unregistered item {component} ignored",
                UserWarning,
                stacklevel=2,
                source=self
            )

    def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None:
        """
        registers the failure to be reported.

        :param source: the title of the reporter object.
        :param input: the value that caused the failure.
        :param error: the risen exception.
        :param fatal: True if the error is from a required component
        """
        failure = {'source': source, 'input': input, 'error': error, 'fatal': fatal}
        self.failures.append(failure)
        for handler in self.failure_handlers:
            handler(failure)

    def make(self) -> ReportDetails:
        """
        builds a report dictionary with the following information;

        **rate** *(float)*
            number between 0.0 - 1.0 ratio of registered success over total.

        **expected_rate** *(float)*
            number between 0.0 - 1.0 ratio of registered success over total required.

        **succeeded** *(int)*
            number of reported successful operations.

        **missed** *(int)*
            number of expected but not reported operations.

        **failed** *(int)*
            number of reported failing operations.

        **total** *(int)*
            number of components expected to succeed.

        **failures** *(list[dict])*
            a list of registered failure (source, input, error).
        """
        completed: float = 0.0
        successes: int = 0
        failures: int = 0
        misses: int = 0
        total: int = len(self.counter)
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
        return ReportDetails(
            rate=round(completed / total, 4),
            expected_rate=round(completed / self.required, 4),
            succeeded=successes,
            missed=misses,
            failed=failures,
            total=total,
            failures=self.failures
        )


def create_report_maker(
        components: Iterable[T],
        log_failures: bool,
        raise_for_fail: bool,
        name: str | None = None,
) -> Callable[[], Report[T]]:
    """
    prepares a report factory to optimize report initialization,
    and tries to detect optional components (components with an attribute 'optional' == True).

    :param components: components that will be reporting (usually chainables)
    :param log_failures: if true, the failures will be logged.
    :param raise_for_fail: if true, an exception will be raised in case of fatal failure.
    :param name: optionally, the name of the reports' owner that will be used in loggings.
    :return: a Report factory, 0-arguments function that returns a report object.
    """
    if not components:
        raise ValueError("unable create reports without components")
    components: frozenset[T] = frozenset(components)
    required: int = [not getattr(component, 'optional', False) for component in components].count(True)
    failure_handlers: list[FailureHandler] = []
    if log_failures:
        failure_handlers.append(LoggingHandler(name))
    if raise_for_fail:
        failure_handlers.append(RaiseFailureHandler(name))
    return lambda: Report(components, required, failure_handlers)
