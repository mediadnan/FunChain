from types import MappingProxyType
from typing import Any, TypedDict, Sequence, TypeVar, Generic

T = TypeVar('T')


class FailureDetails(TypedDict):
    input: Any
    error: Exception


class ReportStats(TypedDict):
    success_rate: float
    succeeded: int
    missed: int
    failed: int
    expected: int
    failures: dict[str, FailureDetails]


class Reporter(Generic[T]):
    __slots__ = '__counter', '__components', '__failures', 'name'

    def __init__(self, components: Sequence[T] = (), name: str | None = None):
        self.name: str | None = name
        self.__components: set[T] = set(components)
        self.__counter: dict[T, list[bool]] = {}
        self.__failures: dict[str, FailureDetails] = {}

    def reset(self):
        """removes all the records"""
        self.__counter = {}
        self.__failures = {}

    def _count(self, source: T, success: bool) -> None:
        if source in self.__counter:
            self.__counter[source].append(success)
        else:
            self.__counter[source] = [success]

    def success(self, source: T) -> None:
        """
        mark operation as successful.

        :param source: the object marking this success.
        """
        self._count(source, True)

    def failed(
            self,
            source: T,
            *,
            input: Any,
            error: Exception,
            ignore: bool = False
    ) -> None:
        """
        mark operation as failed.

        :param source: the object marking this failure.
        :param input: the value that caused this failure.
        :param error: the risen exception that contains details of the failure.
        :param ignore: whether to ignore the failure or not, default to False.
        """
        self._count(source, False)
        if not ignore:
            self.__failures[source] = FailureDetails(input=input, error=error)

    def report(self) -> ReportStats:
        """
        builds a report dictionary with the following information

        **success_rate** *(float)*
            number between 0.0 - 1.0 ratio of registered success over expected success

        **succeeded** *(int)*
            number of reported successful operations.

        **missed** *(int)*
            number of expected but not reported operations.

        **failed** *(int)*
            number of reported failing operations.

        **expected** *(int)*
            number of components expected to succeed.

        **failures** *(dict)*
            dictionary mapping titles (str) to failing details (dict)
            containing "input" value and "error" exception
        """
        completed: float = 0.0
        succeeded: int = 0
        failed: int = 0
        missed: int = 0
        total: int = len(self.__components)
        for results in self.__counter.values():
            succeeded += results.count(True)
            failed += results.count(False)
        for node in self.__components:
            if node in self.__counter:
                counter = self.__counter[node]
                completed += counter.count(True) / len(counter)
            else:
                missed += 1
        try:
            success_rate = completed / total
        except ZeroDivisionError:
            success_rate = 0
        return {
            "success_rate": success_rate,
            "succeeded": succeeded,
            "missed": missed,
            "failed": failed,
            "expected": total,
            "failures": self.__failures.copy()
        }

    def __str__(self) -> str:
        """prettifies the report data"""
        name = self.name
        report = self.report()
        successes, misses, fails, failures = report['succeeded'], report['missed'], report['failed'], report['failures']
        del report
        missed = f", and {misses} components was missed." if misses else '.'
        del misses
        title = f"Report{f' {name!r}' if name else ''}"
        del name
        lines = [
            title,
            '=' * len(title),
            "Completed {round(report['success_rate'] * 100)}% of expected operations.",
            f"Registered {successes} successes and {fails} failures{missed}",
        ]
        if failures:
            lines.extend(("Registered failures", '-' * 19))
            for source, failure in failures.items():
                input, error = failure['input'], failure['error']
                lines.extend((
                    f"- {source}:",
                    f"     input:      {input!r}",
                    f"     input_type: {type(input)}",
                    f"     error:      {error!r}"
                ))
        return '\n'.join(lines)

    def add_components(self, *components: T) -> None:
        """adds expected to succeed components"""
        if not components:
            return
        self.__components |= components

    @property
    def failures(self) -> MappingProxyType[str, FailureDetails]:
        """gets a view of the registered failures - readonly"""
        return MappingProxyType(self.__failures)

    @property
    def counter(self) -> MappingProxyType[T, list[bool]]:
        """gets a view of the counter - readonly"""
        return MappingProxyType(self.__counter)

    @property
    def components(self) -> frozenset[T]:
        """gets a view of the expected components - readonly"""
        return frozenset(self.__components)
