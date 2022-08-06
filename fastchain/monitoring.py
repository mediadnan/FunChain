"""
This module holds implementations of all the monitoring tools that collect
data processing statistics from chainables.
"""
import abc
import warnings
import logging
import typing as tp

from fastchain._abc import ReporterBase

if tp.TYPE_CHECKING:
    from fastchain.chainables import Chainable
else:
    Chainable = tp.Any


class FailureDetails(tp.TypedDict):
    """standard failure details dictionary"""
    source: str
    input: tp.Any
    error: Exception
    fatal: bool


class ReportDetails(tp.TypedDict):
    """standard report details dictionary"""
    rate: float
    expected_rate: float
    succeeded: int
    missed: int
    failed: int
    total: int
    failures: list[FailureDetails]


class FailureHandler(abc.ABC):
    __slots__ = 'owner',

    def __init__(self, owner: str) -> None:
        if owner is None:
            raise ValueError(f"cannot create a {self.name} without owners name")
        self.owner: str = owner

    def message(self, failure: FailureDetails) -> str:
        source, input, error = failure['source'], failure['input'], failure['error']
        return f"{self.owner}::{source} raised {error!r} after receiving {input!r} (type: {type(input).__qualname__})"

    @abc.abstractmethod
    def __call__(self, failure: FailureDetails) -> None: pass
    @property
    @abc.abstractmethod
    def name(self) -> str: pass


class LoggingHandler(FailureHandler):
    name: str = "logging handler"

    def __init__(self, owner: str) -> None:
        super().__init__(owner)
        fmt = logging.Formatter("%(levelname)s %(message)s at %(asctime)s ", "%Y-%m-%d %H:%M:%S", '%')
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger = logging.getLogger(owner)
        logger.addHandler(sh)
        self.logger: logging.Logger = logger

    def __call__(self, failure: FailureDetails) -> None:
        lvl = logging.ERROR if failure['fatal'] else logging.INFO
        self.logger.log(lvl, self.message(failure), stacklevel=2)


class Reporter(ReporterBase):
    """
    Reporter objects get created internally by the chain when it gets called
    to keep track of the execution information and stats between node calls,
    register failures' exceptions and call registered handlers on them, and also
    make a statistics report at the end.

    Users are not supposed to create Reporter object this should be handled by
    the chain and utilities that the chain uses unless the intentions are testing.
    """
    __slots__ = 'counter', 'required', 'failures', 'failure_handlers',

    def __init__(
            self,
            components: frozenset[Chainable],
            required: int,
            failure_handlers: list[FailureHandler]
    ) -> None:
        self.counter: dict[Chainable, list[bool]] = {component: [] for component in components}
        self.required: int = required
        self.failures: list[FailureDetails] = []
        self.failure_handlers: list[FailureHandler] = failure_handlers

    def __call__(self, component: Chainable, success: bool) -> None:
        """
        marks the registered component result as success or failure for statistics.

        :param component: one of the previously registered counter.
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

    def register_failure(
            self,
            source: str,
            input: tp.Any,
            error: Exception,
            fatal: bool = False
    ) -> None:
        """
        registers the failure to be reported.

        :param source: the title of the reporter object.
        :param input: the value that caused the failure.
        :param error: the risen exception.
        :param fatal: True if the error is from a required component
        """
        failure = dict(source=source, input=input, error=error, fatal=fatal)
        self.failures.append(failure)
        for handler in self.failure_handlers:
            handler(failure)

    def report(self) -> ReportDetails:
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
            number of counter expected to succeed.

        **failures** *(list[dict])*
            a list of registered failure (source, input, error).
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
            rate=round(completed / total, 4),
            expected_rate=round(self.required / total, 4),
            succeeded=successes,
            missed=misses,
            failed=failures,
            total=total,
            failures=self.failures
        )


class ReporterMaker:
    """
    ReporterMaker object is a reporter factory that prepares its initial information
    to optimize its initialization when the chain get called.
    """
    __slots__ = 'components', 'required', 'failure_handlers'

    def __init__(self, name: str, components: tp.Iterable[Chainable], handlers: list[tp.Type[FailureHandler]]) -> None:
        """
        Initializes a new ReporterMaker object with the given information.

        :param name: the name of the owner.
        :type name: str
        :param components: chainables that will be reporting.
        :type components: Iterable[Chainable]
        :param handlers: a list of FailureHandler subclasses to handle failures.
        :type handlers: list[FailureHandler]
        """
        if not components:
            raise ValueError("unable create reports without counter")
        self.components: frozenset[Chainable] = frozenset(components)
        self.required: int = [not getattr(component, 'optional', False) for component in self.components].count(True)
        self.failure_handlers: list[FailureHandler] = [handler(name) for handler in handlers]

    def __call__(self) -> Reporter:
        """creates a new Reporter object with the previously specified information."""
        return Reporter(self.components, self.required, self.failure_handlers)
