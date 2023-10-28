from pytest import mark, param
from asyncio import iscoroutine, run
from funchain import nodes, build, chain, foreach


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


test_cases = [
    # Testing simple nodes creation and execution
    param('chain()', 5, 5, nodes.PassiveNode, id="empty node"),
    param('chain(increment)', 3, 4, nodes.Node, id="single node function"),
    param('chain(Add(1))', 3, 4, nodes.Node, id="single node from callable"),
    param('chain(add(1))', 3, 4, nodes.Node, id="single node from function factory"),
    param('chain(increment, double)', 3, 8, nodes.NodeChain, id="chain with two function nodes"),
    param('build(increment) | build(double)', 3, 8, nodes.NodeChain, id="chain with two function nodes with |"),
    param('chain(increment, increment, increment, increment, increment)', 2, 2 + 5, nodes.NodeChain, id="chain with multiple function nodes"),
    param('build(double) * chain(increment)', [3], [4, 4], nodes.NodeChain, id="chain with spread results with *"),
    param('chain(double, foreach(increment))', [3], [4, 4], nodes.NodeChain, id="chain with spread results with foreach"),
    param('chain(foreach(increment), sum)', [3, 4], 9, nodes.NodeChain, id="chain with spread results wrapped"),
    param('chain(foreach((increment, double)), sum)', [3, 4], 18, nodes.NodeChain, id="chain with iterating sub chain"),
    param('build({"double": double, "increment": increment})', 7, {'double': 14, 'increment': 8}, nodes.NodeDict, id="simple node (dict) group"),
    param('build([increment, double])', 7, [8, 14], nodes.NodeList, id="simple node (list) group"),
    param('build({"double": double, "increment": chain(increment, increment)})', 7, {'double': 14, 'increment': 9}, nodes.NodeDict, id="node (dict) group with chain"),
    param('chain([double, chain(increment, increment)])', 7, [14, 9], nodes.NodeList, id="node (list) group with chain"),

    # Testing async nodes creation and execution
    param('build(a_increment)', 3, 4, nodes.AsyncNode, id="single async node function"),
    param('chain(a_increment, a_increment)', 3, 5, nodes.AsyncChain, id="chain of two async functions"),
    param('chain(increment, a_increment)', 3, 5, nodes.AsyncChain, id="chain of sync to async func"),
    param('build(increment) | build(a_increment)', 3, 5, nodes.AsyncChain, id="chain of sync to async func separated nodes"),
    param('build(a_increment) | build(increment)', 3, 5, nodes.AsyncChain, id="chain of async to sync func"),
    param('foreach(a_increment)', [3, 4, 5], (4, 5, 6), nodes.AsyncLoop, id="chain of iterating async func"),
    param('chain(foreach(a_increment), sum)', [3, 4, 5], 15, nodes.AsyncChain, id="chain of iterating async func wrapped"),
    param('build({"ai": a_increment, "i": increment})', 7, {'ai': 8, 'i': 8}, nodes.AsyncDictGroup, id="async - sync node (dict) group"),
    param('build([a_increment, increment])', 7, [8, 8], nodes.AsyncGroup, id="async - sync node (list) group"),
    param('build({"ai": a_increment, "ai2": a_increment})', 7, {'ai': 8, 'ai2': 8}, nodes.AsyncDictGroup, id="async - async node (dict) group"),
    param('build([a_increment, a_increment])', 7, [8, 8], nodes.AsyncGroup, id="async - async node (list) group"),
]


# tests
@mark.parametrize('src, inp, out, tp', test_cases)
def test_node_function(src, inp, out, tp, reporter):
    function = eval(src)
    assert isinstance(function, nodes.BaseNode), "nodes should be instance of BaseNode"
    assert isinstance(function, tp), "node got wrong type"
    result = function(inp, reporter)
    if iscoroutine(result):
        result = run(result)
    assert result == out, "node outputted an unexpected value"
