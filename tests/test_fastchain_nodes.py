import pytest
from asyncio import iscoroutine, run
from fastchain import node, nodes


# fixtures

def increment(number: int) -> int:
    return number + 1


def double(number: int) -> int:
    return number * 2


class Add:  # OOP style factory
    def __init__(self, number: int):
        self.number = number

    def __call__(self, number: int) -> int:
        return self.number + number


def add(number: int):   # functional style factory
    def _add(num: int) -> int:
        return number + num
    return _add


# tests

@pytest.mark.parametrize('src, inp, out, ln, tp', [
    ('node()', 5, 5, 0, nodes.Chain),
    ('node(increment)', 3, 4, 1, nodes.Node),
    ('node(Add(1))', 3, 4, 1, nodes.Node),
    ('node(add(1))', 3, 4, 1, nodes.Node),
    ('node(increment) | double', 3, 8, 2, nodes.Chain),
    ('node(increment) | increment | increment | increment | increment', 2, 2+5, 5, nodes.Chain),
    ('node(double) * increment', [3], [4, 4], 2, nodes.Chain),
    ('node() * increment | sum', [3, 4], 9, 2, nodes.Chain),
    ('node() * (node(increment) | double) | sum', [3, 4], 18, 3, nodes.Chain),
    ('node({"double": double, "increment": increment})', 7, {'double': 14, 'increment': 8}, 2, nodes.DictModel),
    ('node({"double": double, "increment": node(increment) | increment})', 7, {'double': 14, 'increment': 9}, 3, nodes.DictModel),

], ids=str)
def test_node_function(src, inp, out, ln, tp):
    function = eval(src)
    assert isinstance(function, nodes.BaseNode), "nodes should be instance of BaseNode"
    assert isinstance(function, tp), "node got wrong type"
    assert len(function) == ln, "node got wrong length"
    result = function(inp, name='test', handler=None)
    if iscoroutine(result):
        result = run(result)
    assert result == out, "node outputted an unexpected value"
