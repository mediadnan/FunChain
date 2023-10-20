import pytest
from asyncio import iscoroutine, run
from src import nodes


# fixtures

def increment(number: int) -> int:
    return number + 1


async def a_increment(number: int) -> int:
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
    # Testing simple nodes creation and execution
    pytest.param('node()', 5, 5, 0, nodes.Chain, id="empty node"),
    pytest.param('node(increment)', 3, 4, 1, nodes.Node, id="single node function"),
    pytest.param('node(Add(1))', 3, 4, 1, nodes.Node, id="single node from callable"),
    pytest.param('node(add(1))', 3, 4, 1, nodes.Node, id="single node from function factory"),
    pytest.param('node(increment) | double', 3, 8, 2, nodes.Chain, id="chain with two function nodes"),
    pytest.param('node(increment) | increment | increment | increment | increment', 2, 2 + 5, 5, nodes.Chain, id="chain with multiple function nodes"),
    pytest.param('node(double) * increment', [3], [4, 4], 2, nodes.Chain, id="chain with spread results"),
    pytest.param('node() * increment | sum', [3, 4], 9, 2, nodes.Chain, id="chain with spread results wrapped"),
    pytest.param('node() * (node(increment) | double) | sum', [3, 4], 18, 3, nodes.Chain, id="chain with iterating sub chain"),
    pytest.param('node({"double": double, "increment": increment})', 7, {'double': 14, 'increment': 8}, 2, nodes.DictGroup, id="simple node (dict) group"),
    pytest.param('node([increment, double])', 7, [8, 14], 2, nodes.ListGroup, id="simple node (list) group"),
    pytest.param('node({"double": double, "increment": node(increment) | increment})', 7, {'double': 14, 'increment': 9}, 3, nodes.DictGroup, id="node (dict) group with chain"),
    pytest.param('node([double, node(increment) | increment])', 7, [14, 9], 3, nodes.ListGroup, id="node (list) group with chain"),

    # Testing async nodes creation and execution
    pytest.param('node(a_increment)', 3, 4, 1, nodes.AsyncNode, id="single async node function"),
    pytest.param('node(a_increment) | a_increment', 3, 5, 2, nodes.AsyncChain, id="chain of two async functions"),
    pytest.param('node(increment) | a_increment', 3, 5, 2, nodes.AsyncChain, id="chain of sync to async func"),
    pytest.param('node(a_increment) | increment', 3, 5, 2, nodes.AsyncChain, id="chain of async to sync func"),
    pytest.param('node() * a_increment', [3, 4, 5], [4, 5, 6], 1, nodes.AsyncChain, id="chain of iterating async func"),
    pytest.param('node() * a_increment | sum', [3, 4, 5], 15, 2, nodes.AsyncChain, id="chain of iterating async func wrapped"),
    pytest.param('node({"ai": a_increment, "i": increment})', 7, {'ai': 8, 'i': 8}, 2, nodes.AsyncDictGroup, id="async - sync node (dict) group"),
    pytest.param('node([a_increment, increment])', 7, [8, 8], 2, nodes.AsyncListGroup, id="async - sync node (list) group"),
    pytest.param('node({"ai": a_increment, "ai2": a_increment})', 7, {'ai': 8, 'ai2': 8}, 2, nodes.AsyncDictGroup, id="async - async node (dict) group"),
    pytest.param('node([a_increment, a_increment])', 7, [8, 8], 2, nodes.AsyncListGroup, id="async - async node (list) group"),

])
def test_node_function(src, inp, out, ln, tp):
    function = eval(src)
    assert isinstance(function, nodes.BaseNode), "nodes should be instance of BaseNode"
    assert isinstance(function, tp), "node got wrong type"
    assert len(function) == ln, "node got wrong length"
    result = function(inp, name='test', handler=None)
    if iscoroutine(result):
        result = run(result)
    assert result == out, "node outputted an unexpected value"
