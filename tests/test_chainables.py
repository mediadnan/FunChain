import pytest

from fastchain.factory import parse
from fastchain.chainables import Node, Pass, Pipe, Model, Group, Match


def func(a): return a


@pytest.mark.parametrize("structure, chainable_type", [
    (..., Pass),
    (func, Node),
    ((func,), Node),
    (('*', func), Node),
    (('*', '?', func), Node),
    (('*', ':', func), Node),
    ((func, func, func), Pipe),
    ((func, '*', func, '?', func), Pipe),
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
    assert isinstance(parse(structure), chainable_type)


@pytest.mark.parametrize("structure, exception", [
    (None, TypeError),
    ((), ValueError),
])
def test_parsing_bad_structures(structure, exception):
    with pytest.raises(exception):
        parse(structure)

