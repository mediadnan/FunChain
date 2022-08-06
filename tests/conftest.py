from typing import Any

import pytest
from fastchain._abc import ReporterBase


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
            self.failures = {}
            self.counter = {}

        def __call__(self, component, success: bool) -> None:
            if component not in self.counter:
                self.counter[component] = []
            self.counter[component].append(success)

        def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None:
            self.failures[source] = dict(input=input, error=error, fatal=fatal)

        def report(self) -> dict[str, Any]:
            pass
    return TestReporter()
