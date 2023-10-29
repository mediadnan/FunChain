import pytest
from typing import Any
from asyncio import run
from funchain import core, chain, loop, BaseNode, optional, required, static, node


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
        self.__name__ = f"Add({number})"

    def __call__(self, number: int) -> int:
        return self.number + number


def add(number: int):  # functional style factory
    def _add(num: int) -> int:
        return number + num

    _add.__name__ = f'add({number})'
    return _add


test_cases: list[tuple[str, Any, Any]] = [
    # Testing simple nodes creation and execution
    ('chain()', 5, 5),
    ('chain(increment)', 3, 4),
    ('chain(Add(1))', 3, 4),
    ('chain(add(1))', 3, 4),
    ('chain(increment, double)', 3, 8),
    ('chain(increment) + double', 3, 8),
    ('chain(increment, increment, increment, increment, increment)', 2, 2 + 5),
    ('chain(double) * chain(increment)', [3], [4, 4]),
    ('chain(double) * increment', [3], [4, 4]),
    ('chain(double, loop(increment))', [3], [4, 4]),
    ('chain(loop(increment), sum)', [3, 4], 9),
    ('loop(increment) + sum', [3, 4], 9),
    ('chain(loop(increment, double), sum)', [3, 4], 18),
    ('loop(increment, double) + sum', [3, 4], 18),
    ('chain({"d": double, "i": increment})', 7, {'d': 14, 'i': 8}),
    ('chain([increment, double])', 7, [8, 14]),
    ('chain({"d": double, "i": (increment, increment)})', 7, {'d': 14, 'i': 9}),
    ('chain([double, chain(increment, increment)])', 7, [14, 9]),

    # Testing async nodes creation and execution
    ('chain(a_increment)', 3, 4),
    ('chain(a_increment, a_increment)', 3, 5),
    ('chain(increment, a_increment)', 3, 5),
    ('chain(increment) + chain(a_increment)', 3, 5),
    ('chain(a_increment) + chain(increment)', 3, 5),
    ('loop(a_increment)', [3, 4, 5], (4, 5, 6)),
    ('chain(loop(a_increment), sum)', [3, 4, 5], 15),
    ('chain({"ai": a_increment, "i": increment})', 7, {'ai': 8, 'i': 8}),
    ('chain([a_increment, increment])', 7, [8, 8]),
    ('chain({"ai": a_increment, "ai2": a_increment})', 7, {'ai': 8, 'ai2': 8}),
    ('chain([a_increment, a_increment])', 7, [8, 8]),
]


# tests
@pytest.mark.parametrize('src, inp, out', test_cases, ids=[i[0] for i in test_cases])
def test_node_chains(src, inp, out, reporter):
    """Test nodes created with chain() function and with and without reporter"""
    nd = eval(src)
    assert isinstance(nd, BaseNode), "chain() returned an unexpected type"
    res = run(nd(inp)) if nd.is_async else nd(inp)
    assert res == out, "node without reporter outputted an unexpected value"
    res = run(nd(inp, reporter)) if nd.is_async else nd(inp, reporter)
    assert res == out, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"


def test_optional_node_in_a_chain(reporter):
    """Tests if the optional node is skipped in case of failure without reporting"""
    nd = chain(optional(increment), double)
    assert nd(3) == 8, "node outputted an unexpected value"
    assert nd("3", reporter) == "33", "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"


def test_normal_node_in_a_chain(reporter):
    """Tests if the normal node is skipped in case of failure while reporting"""
    nd = chain(increment, double)
    assert nd(3) == 8, "node outputted an unexpected value"
    assert nd("3", reporter) is None, "node outputted an unexpected value"
    assert len(reporter.failures), "node reported failures while it shouldn't"


def test_required_node_in_a_chain(reporter):
    """Tests if the required node cause the entire chain to fail in case of failure while reporting"""
    nd = chain(required(increment), double)
    assert nd(3) == 8, "node outputted an unexpected value"
    assert nd("3", reporter) is None, "node outputted an unexpected value"
    assert len(reporter.failures) == 1, "node didn't report failure while it should"


def test_optional_node_in_a_node_dict(reporter):
    """Tests if the optional node is skipped in case of failure without reporting"""
    nd = chain({"i": optional(increment), "d": double})
    assert nd(3) == {'i': 4, 'd': 6}, "node outputted an unexpected value"
    assert nd("3", reporter) == {'d': "33"}, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"


def test_required_node_in_a_node_dict(reporter):
    """Tests if the required node cause the entire node to fail in case of failure while reporting"""
    nd = chain({"i": required(increment), "d": double})
    assert nd(3) == {'i': 4, 'd': 6}, "node outputted an unexpected value"
    assert nd("3", reporter) is None, "node outputted an unexpected value"
    assert len(reporter.failures) == 1, "node didn't report failure while it should"


def test_normal_node_in_a_node_dict(reporter):
    """Tests if the normal node returns None in case of failure while reporting"""
    nd = chain({"i": increment, "d": double})
    assert nd(3) == {'i': 4, 'd': 6}, "node outputted an unexpected value"
    assert nd("3", reporter) == {'i': None, 'd': "33"}, "node outputted an unexpected value"
    assert len(reporter.failures) == 1, "node didn't report failure while it should"


def test_optional_node_in_a_node_list(reporter):
    """Tests if the optional node is skipped in case of failure without reporting"""
    nd = chain([optional(increment), double])
    assert nd(3) == [4, 6], "node outputted an unexpected value"
    assert nd("3", reporter) == ["33"], "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"


def test_required_node_in_a_node_list(reporter):
    """Tests if the required node cause the entire node to fail in case of failure while reporting"""
    nd = chain([required(increment), double])
    assert nd(3) == [4, 6], "node outputted an unexpected value"
    assert nd("3", reporter) is None, "node outputted an unexpected value"
    assert len(reporter.failures) == 1, "node didn't report failure while it should"


def test_normal_node_in_a_node_list(reporter):
    """Tests if the normal node returns None in case of failure while reporting"""
    nd = chain([increment, double])
    assert nd(3) == [4, 6], "node outputted an unexpected value"
    assert nd("3", reporter) == [None, "33"], "node outputted an unexpected value"
    assert len(reporter.failures) == 1, "node didn't report failure while it should"


def test_static_node():
    obj = object()
    assert chain(3)(None) == 3, "node outputted an unexpected value"
    assert chain(None)(None) is None, "node outputted an unexpected value"
    assert chain(obj)(None) is obj, "node outputted an unexpected value"
    model = [increment, double]
    nd = chain(model)
    assert nd(3) == [4, 6], "node outputted an unexpected value"
    nd = chain(static(model))
    assert nd(3) is model, "node outputted an unexpected value"


@pytest.mark.parametrize("fun, is_async, given_name, name", [
    (increment, False, None, "increment"),
    (increment, False, "inc", "inc"),
    (a_increment, True, None, "a_increment"),
    (a_increment, True, "ai", "ai"),
    (Add(5),  False, None, "Add(5)"),
    (Add(5),  False, "add_5", "add_5"),
    (add(5), False, None, "add(5)"),
    (add(5), False, "add_5", "add_5"),
    (double, False, None, "double"),
])
def test_node_functions(fun, is_async, given_name, name):
    """Tests if the node functions are correctly created"""
    nd = node(fun, given_name)
    assert isinstance(nd, core.Node), "node() returned an unexpected type"
    assert nd.is_async is is_async, "node got a wring is_async value"
    assert isinstance(nd, core.AsyncNode) is is_async,  "node() returned an unexpected type"
    assert nd.fun is fun,  "node() returned an unexpected function"
    assert nd.name == name,  "node() returned an unexpected name"
    nd = nd.rn("new_name")
    assert nd.name == "new_name",   "node() didn't get renamed correctly"
    assert isinstance(nd, core.Node),  "node() returned an unexpected type"
