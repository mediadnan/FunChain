import pytest
from fastchain.monitoring import Reporter


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


@pytest.fixture
def reporter():
    """returns a new reporter"""
    return Reporter()
