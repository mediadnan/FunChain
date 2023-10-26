import pytest
from funchain import chain, build
from funchain.nodes import BaseNode, Node, Severity


def double(number: int) -> int:
    """Doubles the number and returns the result"""
    return number * 2


# testing nd() function
def test_nd_for_lambda():
    node = build(lambda x: x*2)
    assert isinstance(node, BaseNode), "Expected node to be of type BaseNode"
    assert isinstance(node, Node), "Expected node to be of type Node"
    assert node.name == "lambda", "Expected default name to be 'lambda'"
    assert node.severity is Severity.NORMAL, "Expected default severity to be NORMAL"


@pytest.mark.parametrize('src', [
    'build(...)',
    'build(lambda x: x*2)',
    'build(double)',
    'build({\'a\': double, \'b\': lambda x: x - 1})',
    'build([double, lambda x: x - 1])',
    'chain(double, double)',
    'build(double) | build(double)',
    'build(double) | build([lambda x: x + 1, lambda x: x - 1, double]) * build(double)'
])
def test_nd_default_severity(src: str):
    node = eval(src)
    assert node.severity is Severity.NORMAL, "Expected default severity to be NORMAL"


def test_single_inline_node_function(reporter):
    node = build(lambda x: x * 2).rn("double")
    result = node(3, reporter=reporter)
    assert result == 6
