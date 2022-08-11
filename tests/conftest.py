from typing import Any

import pytest
from fastchain._abc import ReporterBase  # noqa
from fastchain.chainables import Chainable
from fastchain.monitoring import FailureDetails


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


@pytest.fixture(scope='session')
def fake_error():
    return Exception('test error')


@pytest.fixture
def fail(fake_error):
    def fl(*_, **__):
        raise fake_error
    fl.__qualname__ = 'fail'
    return fl


@pytest.fixture
def test_reporter():
    class TestReporter(ReporterBase):
        def __init__(self):
            self.failures: dict[str, FailureDetails] = {}
            self.counter: dict[Chainable, list[bool]] = {}

        def __call__(self, component: Chainable, success: bool) -> None:
            if component not in self.counter:
                self.counter[component] = [success]
            else:
                self.counter[component].append(success)

        def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None:
            self.failures[source] = dict(source=source, input=input, error=error, fatal=fatal)

        def report(self) -> dict[str, Any]:
            pass

        def clear(self) -> None:
            self.failures = {}
            self.counter = {}

    return TestReporter()
