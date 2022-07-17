import warnings
from types import MappingProxyType
from typing import TypedDict, TypeVar, Generic, Iterable, Any

T = TypeVar('T')


class FailureDetails(TypedDict):
    """standard failure details dictionary"""
    input: Any
    error: Exception


class ReportDetails(TypedDict):
    """standard report details dictionary"""
    rate: float
    expected_rate: float
    succeeded: int
    missed: int
    failed: int
    total: int
    failures: dict[str, FailureDetails]


class Report(Generic[T]):
    __slots__ = (
        '__counter',
        '__required',
        '__failures'
    )

    def __init__(self, components: Iterable[T], required: int | None = None):
        if not components:
            raise ValueError("unable create a stat object without components")
        counter = {component: [] for component in components}
        if required is None:
            required = len(counter)
        self.__counter: dict[T, list[bool]] = counter
        self.__required: int = required
        self.__failures: dict[str, FailureDetails] = {}

    def __call__(self, component: T, success: bool) -> None:
        try:
            self.__counter[component].append(success)
        except KeyError:
            warnings.warn(
                f"unregistered item {component} ignored",
                UserWarning,
                stacklevel=2,
                source=self
            )

    def register_failure(self, reporter: str, failure: FailureDetails) -> None:
        """
        registers the failure to be reported.

        :param reporter: the title of the reporter object.
        :param failure: the failure's details
        """

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

        **failures** *(dict[str, dict])*
            a dictionary mapping reporter title to failure details.
        """
        completed: float = 0.0
        successes: int = 0
        failures: int = 0
        misses: int = 0
        total: int = len(self.__counter)
        for record in self.__counter.values():
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
            expected_rate=round(completed / self.__required, 4),
            succeeded=successes,
            missed=misses,
            failed=failures,
            total=total,
            failures=self.__failures
        )

    @property
    def counter(self) -> MappingProxyType[T, list[bool]]:
        """gets a view of the counter - readonly"""
        return MappingProxyType(self.__counter)
