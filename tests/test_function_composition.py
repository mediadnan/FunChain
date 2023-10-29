import pytest
from funchain import chain, loop


def double(number: int) -> int:
    """Doubles the number and returns the result"""
    return number * 2


# testing nd() function
@pytest.mark.parametrize('src', [
    'chain()',
    'chain(lambda x: x*2)',
    'chain(double)',
    'chain({\'a\': double, \'b\': lambda x: x - 1})',
    'chain([double, lambda x: x - 1])',
    'chain(double, double)',
    'chain(double) * double',
    'chain(double) * [lambda x: x + 1, lambda x: x - 1, double] * double'
])
def test_nd_default_severity(src: str):
    node = eval(src)


def test_multiple_node_group_chain():
    node1 = chain(double) * [lambda x: x + 1, lambda x: x - 1, double] * double
    node2 = chain(double, loop([lambda x: x + 1, lambda x: x - 1, double]), loop(double))
    assert node1([5]) == node2([5])


def test_single_inline_node_function(reporter):
    node = chain(lambda x: x * 2).rn("double")
    result = node(3, reporter=reporter)
    assert result == 6
