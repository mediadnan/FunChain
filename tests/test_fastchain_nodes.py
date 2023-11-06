import failures
import pytest
from asyncio import run

import funchain
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


# tests
@pytest.mark.parametrize(
    "src, err", [
        ("node()", TypeError),
        ("node(None)", TypeError),
    ]
    )
def test_bad_node_chain_structures(src, err):
    """Tests wrong usage of funchain functions"""
    with pytest.raises(err):
        eval(src)


@pytest.mark.parametrize("input", [3, None, object(), "2"], ids=lambda x: f'passive({x})')
def test_empty_chain_passive_node(input, reporter):
    nd = chain()
    assert nd(input) is input, "node outputted an unexpected value"
    assert nd(input, reporter) is input, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"


@pytest.mark.parametrize("fun, inp, out, label", [
    ("increment", 3, 4, "increment"),
    ("Add(1)", 3, 4, "Add(1)"),
    ("add(1)", 3, 4, "add(1)"),
    ("double", 3, 6, "double"),
    ("node(increment)", 4, 5, "increment"),
    ("node(double)", 4, 8, "double"),
    ("lambda x: x + 1", 4, 5, "lambda"),
    ("lambda x: x * 2", 4, 8, "lambda"),
])
@pytest.mark.parametrize("src", ["node({fun})", "chain({fun})"])
def test_single_function_node(src, fun, inp, out, label, reporter):
    nd = eval(src.format(fun=fun))
    assert isinstance(nd, funchain.core.Node), f"{src} returned an unexpected type"
    assert nd(inp) == out, "node outputted an unexpected value"
    assert nd(inp, reporter) == out, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"
    assert nd(None, reporter) is None, "node outputted an unexpected value"
    assert reporter.failures.pop().source == f"test.{label}", "node reported a failure with wrong source tag"
    nd = nd.rn("my_function")
    assert nd.name == "my_function", "node name is not set correctly"


@pytest.mark.parametrize("src", ["chain(a_increment)", "node(a_increment)"])
@pytest.mark.asyncio
async def test_async_single_function_node(src, reporter):
    nd = eval(src)
    assert isinstance(nd, funchain.core.AsyncNode), f"{src} returned an unexpected type"
    assert (await nd(3)) == 4, "node outputted an unexpected value"
    assert (await nd(3, reporter)) == 4, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"
    nd = nd.rn("my_function")
    assert nd.name == "my_function", "node name is not set correctly"


@pytest.mark.parametrize("src, inp, out", [
    ("chain(increment, double)", 3, 8),
    ("chain(increment) | double", 3, 8),
    ("chain(increment, increment, increment, increment, increment)", 2, 2 + 5),
    ("chain(double) * chain(increment)", [3], [4, 4]),
    ("chain(double) * increment", [3], [4, 4]),
    ("chain(double, loop(increment))", [3], [4, 4]),
    ("loop(increment) | sum", [3, 4], 9),
    ("chain(loop(increment, double), sum)", [3, 4], 18),
    ("loop(increment, double) | sum", [3, 4], 18),
])
def test_sequential_node_chain(src, inp, out, reporter):
    nd = eval(src)
    assert not nd.is_async, "The result chain must be sync"
    assert isinstance(nd, funchain.core.NodeChain), f"{src} returned an unexpected type"
    assert nd(inp) == out, "node outputted an unexpected value"
    assert nd(inp, reporter) == out, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"
    assert nd(None, reporter) is None, "node outputted an unexpected value"
    new = nd.rn("my_function")
    assert new.name == "my_function", "node name is not set correctly"  # noqa


@pytest.mark.parametrize("src, inp, out", [
    ('chain(a_increment, a_increment)', 3, 5),
    ('chain(increment, a_increment)', 3, 5),
    ('chain(increment) | chain(a_increment)', 3, 5),
    ('chain(a_increment) | chain(increment)', 3, 5),
    ('loop(a_increment) | double', [3, 4, 5], [4, 5, 6, 4, 5, 6]),
    ('chain(loop(a_increment), sum)', [3, 4, 5], 15),
    ('(chain() * a_increment) | sum', [3, 4, 5], 15),
])
@pytest.mark.asyncio
async def test_async_sequential_node_chain(src, inp, out, reporter):
    nd = eval(src)
    assert nd.is_async, "The result chain must be async"
    assert isinstance(nd, funchain.core.NodeChain), f"{src} returned an unexpected type"
    assert (await nd(inp)) == out, "node outputted an unexpected value"
    assert (await nd(inp, reporter)) == out, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"
    assert (await nd(None, reporter)) is None, "node outputted an unexpected value"
    new = nd.rn("my_function")
    assert new.name == "my_function", "node name is not set correctly"  # noqa
    # TODO: Check for failure label


@pytest.mark.parametrize("src, inp, out", [
    ('chain({"d": double, "i": increment})', 7, {'d': 14, 'i': 8}),
    ('chain([increment, double])', 7, [8, 14]),
    ('chain({"d": double, "i": (increment, increment)})', 7, {'d': 14, 'i': 9}),
    ('chain([double, chain(increment, increment)])', 7, [14, 9]),
])
def test_node_model(src, inp, out, reporter):
    nd = eval(src)
    assert isinstance(nd, (funchain.core.NodeDict, funchain.core.NodeList)), f"{src} returned an unexpected type"
    assert nd(inp) == out, "node outputted an unexpected value"
    assert nd(inp, reporter) == out, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"
    assert nd(None, reporter) is None, "node outputted an unexpected value"
    new = nd.rn("my_function")
    assert new.name == "my_function", "node name is not set correctly"  # noqa


@pytest.mark.parametrize("src, inp, out", [
    ('chain({"ai": a_increment, "i": increment})', 7, {'ai': 8, 'i': 8}),
    ('chain([a_increment, increment])', 7, [8, 8]),
    ('chain({"ai": a_increment, "ai2": a_increment})', 7, {'ai': 8, 'ai2': 8}),
    ('chain([a_increment, a_increment])', 7, [8, 8]),
])
@pytest.mark.asyncio
async def test_async_node_model(src, inp, out, reporter):
    nd = eval(src)
    assert isinstance(nd, (funchain.core.NodeDict, funchain.core.NodeList)), f"{src} returned an unexpected type"
    assert (await nd(inp)) == out, "node outputted an unexpected value"
    assert (await nd(inp, reporter)) == out, "node outputted an unexpected value"
    assert not reporter.failures, "node reported failures while it shouldn't"
    assert (await nd(None, reporter)) is None, "node outputted an unexpected value"
    new = nd.rn("my_function")
    assert new.name == "my_function", "node name is not set correctly"  # noqa


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
    with pytest.raises(failures.FailureException):
        nd("3", reporter)


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
    with pytest.raises(failures.FailureException):
        nd("3", reporter)


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
    with pytest.raises(failures.FailureException):
        nd("3", reporter)


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
