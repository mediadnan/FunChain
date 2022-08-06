import pytest

from fastchain.chain import Chain
from fastchain.chainables import Node, Pass, Sequence, Model, Group, Match


def func(a): return a
def increment(x): return x + 1
def double(x): return x*2
def fail(x): raise Exception(f"I've failed with {x}")


@pytest.mark.parametrize("structure, chainable_type", [
    (..., Pass),
    (func, Node),
    ((func,), Node),
    (('*', func), Node),
    (('*', '?', func), Node),
    (('*', ':', func), Node),
    ((func, func, func), Sequence),
    ((func, '*', func, '?', func), Sequence),
    ({'key1': func, 'key2': func}, Model),
    (('*', {'key1': func, 'key2': func}, ), Model),
    (('?', {'key1': func, 'key2': func}, ), Model),
    ({'key1': func, 'key2': (func, func, {'key1': func, 'key2': func})}, Model),
    ((':', {'key1': func, 'key2': func}), Model),
    ([func, func], Group),
    (([func, func],), Group),
    (('?', [func, func],), Group),
    (('*', [func, func],), Group),
    ((':', [func, func],), Match),
    ((':', '*', [func, func],), Match),
])
def test_parsing_node(structure, chainable_type):
    assert isinstance(Chain.parse(structure), chainable_type)


@pytest.mark.parametrize("structure, exception", [
    (None, TypeError),
    ((), ValueError),
])
def test_parsing_bad_structures(structure, exception):
    with pytest.raises(exception):
        Chain.parse(structure)


@pytest.mark.parametrize("body, input, output", [
    ((increment, ), 3, 4),
    ((increment, double), 3, 8),
    ((increment, '?', double), 3, 8),
    ((increment, '?', fail), 3, 4),
    ((increment, fail), 3, None),
    ((double, '*', double, list), [3, 4, 5], [6, 8, 10, 6, 8, 10]),
    (('*', increment, list, double), [3, 4, 5], [4, 5, 6, 4, 5, 6]),
    (('*', (increment, double), list), [3, 4, 5], [8, 10, 12]),
    (({'inc': increment, 'dub': double, 'dub-inc': (double, increment)},), 2, {'inc': 3, 'dub': 4, 'dub-inc': 5}),
    (([increment, double, (double, increment)],), 2, [3, 4, 5]),
    ((dict.items, '*', ':', [str.upper, double], dict), {"key1": 1, "key2": 2}, {"KEY1": 2, "KEY2": 4}),

])
def test_results(body, input, output):
    chain = Chain('test', *body, log_failures=False)
    assert chain(input) == output
