from pytest import fixture
from funchain import Reporter


@fixture
def reporter():
    """Returns a new empty reporter"""
    return Reporter("test")
