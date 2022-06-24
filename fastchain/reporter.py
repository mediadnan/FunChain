from math import floor
from pprint import pformat
from typing import (
    Dict,
    Any,
    Callable,
    Generator,
    List,
    Optional
)

REPORT_CALLBACK = Callable[['Report'], None]


class Report:
    __lw: int = 80
    __title: str
    __total: int
    __completed: Dict[Any, int]
    __failures: Dict[Any, List[Dict[str, Any]]]

    def __init__(
            self,
            title: str,
            completed: Dict[Any, int],
            failures: Dict[Any, List[Dict[str, Any]]],
            total: Optional[int],
    ) -> None:
        self.__title = title
        self.__completed = completed
        self.__failures = failures
        self.__total = max((total or 0, self.completed_components + self.failed_components))

    @property
    def title(self) -> str:
        """gets the report's title - read-only"""
        return self.__title

    @property
    def ok(self) -> bool:
        """true if no failure is registered"""
        return not self.__failures

    @property
    def completed_operations(self) -> int:
        """gets the count of completed operations - read-only"""
        return sum(self.__completed.values())

    @property
    def failed_operations(self) -> int:
        """gets the count of failed operations - read-only"""
        return sum(map(len, self.__failures.values()))

    @property
    def completed_components(self) -> int:
        """gets the count of completed components - read-only"""
        return len(self.__completed)

    @property
    def failed_components(self) -> int:
        """gets the count of failed operations - read-only"""
        return len(self.__failures)

    @property
    def failures(self) -> Dict[str, List[Dict[str, Any]]]:
        """gets the failures' registry - read-only"""
        return {str(source): failures for source, failures in self.__failures.items()}

    @property
    def total(self) -> int:
        """gets the total number of elements - read-only"""
        return self.__total

    @property
    def rate(self) -> float:
        """gets the raw ratio of completed components over total components - read-only"""
        try:
            return self.completed_components / self.__total
        except ZeroDivisionError:
            return 0

    @property
    def summary(self) -> str:
        rt, cmo, cmc, flo, flc = (
            self.rate,
            self.completed_operations,
            self.completed_components,
            self.failed_operations,
            self.failed_components,
        )
        if rt == 0:
            completeness = 'no component has succeeded'
        elif rt == 1:
            completeness = 'all components have succeeded'
        else:
            completeness = f'only {floor(rt * 100)}% of components have succeeded'

        return f"""SUMMARY: {completeness}
    {cmc} completed components ({cmo} completed operations)
    {flc} failed components ({flo} failed operations)"""

    def __str__(self) -> str:
        sep1 = '=' * self.__lw
        return '\n'.join((
            sep1,
            f"REPORT: {self.title!r}",
            self.summary,
            *self._registry_stream(self.failures, 'FAILURES'),
            sep1
        ))

    def _registry_stream(
            self,
            registry: Dict[str, List[Dict[str, Any]]],
            title: str,
    ) -> Generator[str, Any, None]:
        if registry:
            yield '-' * self.__lw
            yield f'{title}:'
        for source, details in registry.items():
            yield f"  {source}:"
            for detail in details:
                lst_ind = '- '
                for key, value in detail.items():
                    line = f"    {lst_ind}{key}: "
                    line += pformat(value, indent=2, width=self.__lw - len(line))
                    yield line
                    lst_ind = '  '


class Reporter:
    _title: str
    _total_expected: Optional[int]
    _completed: Dict[Any, int]
    _failures: Dict[Any, List[Dict[str, Any]]]

    def __init__(self, title: str, total_expected: int = None):
        self._title = title
        self._total_expected = total_expected
        self.reset()

    def success(self, source) -> None:
        """
        registers a successful operation.

        :param source: the object calling this method
        """
        if source not in self._completed:
            self._completed[source] = 0
        self._completed[source] += 1

    def failure(self, source, details: Dict[str, Any]) -> None:
        """
        registers a failed operation.

        :param source: the object calling this method
        :param details: details of the failure; input, error, previous ...
        """
        if source not in self._failures:
            self._failures[source] = []
        self._failures[source].append(details)

    def report(self) -> Report:
        """produces a Report object"""
        return Report(self._title, self._completed, self._failures, self._total_expected)

    def reset(self) -> None:
        """resets all records"""
        self._completed = {}
        self._failures = {}


if __name__ == '__main__':
    report = Reporter('test')
    for _ in range(5):
        report.success('abc')
    report.failure('abc', {})
    print(report.report())
