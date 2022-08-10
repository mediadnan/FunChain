from typing import Type

import pytest
import functools    # noqa (needed in namespace for parametized test)
from pytest import param
from fastchain.factory import *
from fastchain.chainables import *
from fastchain.chainables.base import Pass


def func(*_): pass


class Func:
    def __call__(self, _): pass


@pytest.mark.parametrize('structure, expected_type, length', [
    param('...', Pass, 0, id="chain-pass"),
    param('func', Node, 1, id="normal function"),
    param('Func', Node, 1, id="constructor"),
    param('Func()', Node, 1, id="callable object"),
    param('lambda x: ...', Node, 1, id="lambda"),
    param('functools.partial(func, 3)', Node, 1, id="partial"),
    param('(func,)', Node, 1, id="unnecessary parenthesis"),
    param('("*", func)', Node, 1, id="parenthesis wrapping option"),
    param('("*", "?", func)', Node, 1, id="parenthesis wrapping options"),
    param('(func, func)', Sequence, 2, id="sequence of nodes"),
    param('(func, "*", "?", func)', Sequence, 2, id="sequence of nodes and options"),
    param('(func, (func, func))', Sequence, 3, id="sequence with nested sequence"),
    param('("*", (func, func))', Sequence, 2, id="sequence with option"),

    param('{"key1": func, "key2": func}', DictModel, 2, id="dict_model"),
    param('("*", {"key1": func, "key2": func})', DictModel, 2, id="dict_model with option"),
    param('{"key1": (func, "?", func), "key2": {"key3": func}}', DictModel, 3, id="dict_model with nested structure"),

    param('[func, func]', ListModel, 2, id="list_model"),
    param('("*", [func, func])', ListModel, 2, id="list_model with option"),
    param('[func, (func, func), [func, func]]', ListModel, 5, id="list_model with nested structure"),

    param('match(func, func)', Match, 2, id="match"),
    param('("*", match(func, func))', Match, 2, id="match with option"),
    param('match(func, ("*", func))', Match, 2, id="match has option"),
    param('match(func, (func, func), {"k1": func, "k2": (func, func)})', Match, 6, id="match with nested structure"),
])
def test_parse_function(structure: str, expected_type: Type[Exception], length: int):
    chainable_object = parse(eval(structure))
    assert isinstance(chainable_object, expected_type)
    assert len(chainable_object) == length  # type: ignore


@pytest.mark.parametrize('structure, Error, err_msg', [
    param('None', TypeError, 'unchainable type', id="reject wrong type"),
    param('("unknown_option_for_test", func)', ValueError, 'unknown chain option', id="reject wrong option"),
    param('()', ValueError, 'cannot create.*?sequence', id="reject empty sequence"),
    param('{}', ValueError, 'cannot create.*?model', id="reject empty dict_model"),
    param('[]', ValueError, 'cannot create.*?model', id="reject empty list_model"),
    param('match()', ValueError, 'cannot create.*?match', id="reject empty match"),
    param('match(func)', ValueError, 'cannot create.*?match', id="reject match with single member"),
])
def test_unsupported_types(structure: str, Error: Type[Exception], err_msg: str):
    with pytest.raises(Error, match=err_msg):
        parse(eval(structure))
