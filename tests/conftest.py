from pytest import fixture
from fastchain import monitoring, chains


@fixture
def increment():
    """simple function needed for testing"""
    def func(number: int) -> int:
        return number + 1
    func.__name__ = 'increment'
    func.__qualname__ = 'increment'
    return func


@fixture
def double():
    """alternative function needed for testing"""
    def func(number: int) -> int:
        return number * 2
    func.__name__ = 'double'
    func.__qualname__ = 'double'
    return func


@fixture
def fail():
    """function that does nothing but raises an exception"""
    def func(*_, **__):
        raise Exception("Failed for test")
    func.__name__ = 'fail'
    func.__qualname__ = 'fail'
    return func


@fixture
def reporter():
    """returns a new reporter"""
    return monitoring.Reporter()


@fixture
def mock_registry(monkeypatch):
    monkeypatch.setattr(chains, '_registry_', {})
