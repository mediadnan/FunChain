import itertools
import operator
import pytest
import statistics
from fastchain.chainables import Chainable, Node
from fastchain.chainables.base import ChainableBase
from fastchain.monitoring import Reporter, ReporterBase, FailureDetails, ReportDetails


@pytest.fixture
def increment():
    """simple function needed for testing"""
    def inc(number: int) -> int:
        return number + 1
    inc.__qualname__ = 'increment'
    return inc


@pytest.fixture
def double():
    """alternative function needed for testing"""
    def dbl(number: int) -> int:
        return number * 2
    dbl.__qualname__ = 'double'
    return dbl


@pytest.fixture
def fake_error():
    """exception used for tests"""
    return Exception('test error')


@pytest.fixture
def fail(fake_error):
    """function that does nothing but raises an exception"""
    def fl(*_, **__):
        raise fake_error
    fl.__qualname__ = 'fail'
    return fl


class BasicTestReporter(ReporterBase):
    counter: dict[Chainable, list[bool]]
    failures: list[FailureDetails]

    def __init__(self):
        self.failures = []
        self.counter = {}

    def mark(self, component: Chainable, success: bool) -> None:
        if component not in self.counter:
            self.counter[component] = [success]
        else:
            self.counter[component].append(success)

    def report_failure(self, source: Chainable, input, error: Exception) -> None:
        self.failures.append(dict(source=source.title, input=input, error=error, fatal=not source.optional))

    def report(self) -> ReportDetails:
        return dict(
            rate=round(statistics.mean([statistics.mean(map(int, i)) for i in self.counter.values()])),
            succeeded=operator.countOf(itertools.chain(*self.counter.values()), True),
            failed=operator.countOf(itertools.chain(*self.counter.values()), False),
            missed=0,
            required=len(self.counter),
            total=len(self.counter),
            failures=self.failures
        )

    def clear(self) -> None:
        self.failures = []
        self.counter = {}


class FakeTestReporter(ReporterBase):
    def __init__(self):
        self.mark_called: bool = False
        self.report_failure_called: bool = False

    def mark(self, node: ChainableBase, success: bool) -> None: self.mark_called = True
    def report_failure(self, source: ChainableBase, input, error: Exception) -> None: self.report_failure_called = True
    def report(self) -> ReportDetails: raise NotImplementedError('this functionality is not implemented')


@pytest.fixture
def basic_reporter(): return BasicTestReporter()
@pytest.fixture
def fake_reporter(): return FakeTestReporter()
@pytest.fixture
def nodes(increment): return tuple(Node(increment, name=f'node{i+1}') for i in range(4))
@pytest.fixture
def reporter(nodes): return Reporter(frozenset(nodes), len(nodes))
