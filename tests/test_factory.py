import inspect
import re
from typing import Type, Any, Callable

import pytest
import functools    # noqa (needed in namespace for parametized test)
from pytest import param
from fastchain.factory import *
from fastchain.chainables import *
from fastchain.chainables.base import Pass


# test parsing chainables

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
    param('()', ValueError, 'sequence must contain at least one node', id="reject empty sequence"),
    param('(...,)', ValueError, 'sequence must contain at least one node', id="reject sequence with one pass"),
    param('("*", ...)', ValueError, 'sequence must contain at least one node', id="reject sequence with option on pass"),
    param('(..., ...)', ValueError, 'sequence must contain at least one node', id="reject sequence with multiple pass"),
    param('{}', ValueError, 'cannot create.*?model', id="reject empty dict_model"),
    param('[]', ValueError, 'cannot create.*?model', id="reject empty list_model"),
    param('match()', ValueError, 'cannot create.*?match', id="reject empty match"),
    param('match(func)', ValueError, 'cannot create.*?match', id="reject match with single member"),
    param('match(func, ("?", func))', ValueError, 'cannot.*?optional', id="reject optional match member"),
])
def test_unsupported_types(structure: str, Error: Type[Exception], err_msg: str):
    with pytest.raises(Error, match=err_msg):
        parse(eval(structure))


@pytest.mark.parametrize('source, expected_type', [
    ('sequence(func, func)', Sequence),
    ('dict_model(key1=func, key2=func)', DictModel),
    ('list_model(func, func)', ListModel),
    ('chainable(func)', Node)
])
def test_alternative_explicit_parse_functions(source, expected_type):
    assert isinstance(eval(source), expected_type)


# test chainable utility function
def add(a: int, b: int) -> int: return a + b
def increment(a: int) -> int: return a + 1


@pytest.mark.parametrize('default_kw, default', [
    param({}, None, id="no custom default provided"),
    param({'default': None}, None, id="explicit 'None' default provided"),
    param({'default': 0}, 0, id="custom default 0 provided"),
    param({'default_factory': list}, [], id="custom default_factory for [] provided"),
    param({'default': 0, 'default_factory': str}, '', id="both default and default_factory provided"),
])
@pytest.mark.parametrize('args, kwargs, name', [
    param((increment,), {}, 'increment', id="simple 1arg function only"),
    param((increment,), {'name': 'inc'}, 'inc', id="simple 1arg function only with explicit name"),
    param((lambda x: x+1,), {'name': 'increment'}, 'increment', id="lambda function passed"),
    param((add, 1), {'name': 'increment'}, 'increment', id="partial positional argument passed"),
    param((add,), {'name': 'increment', 'b': 1}, 'increment', id="partial keyword argument passed"),
])
def test_chainable_function_result(args, kwargs, name, default, default_kw, test_reporter):
    node = chainable(*args, **kwargs, **default_kw)  # type: ignore
    assert node.name == name
    assert node.default_factory() == default
    assert node.function(3) == 4
    assert node.process(3, test_reporter) == (True, 4)
    assert node.process(None, test_reporter) == (False, default)


@pytest.mark.parametrize('args, kwargs, Error', [
    param((increment, ), {'default_factory': object()}, TypeError, id='wrong default factory type'),
])
def test_chainable_function_validation(args, kwargs, Error):
    pytest.raises(Error, chainable, *args, **kwargs)  # type: ignore


# test funfact decorator
def test_trying_funfact_over_non_callables():
    with pytest.raises(TypeError, match=r'funfact takes a callable as first argument not .*'):
        funfact(object())


def common_case_check(function_factory, name, default):
    # check decorated function signature properties preservation
    wrapped = getattr(function_factory, '__wrapped__')
    for attr in (
            '__name__',
            '__qualname__',
            '__doc__',
            '__module__',
            '__annotations__',
            '__defaults__',
            '__kwdefaults__'
    ):
        if not hasattr(wrapped, attr):
            continue
        assert getattr(function_factory, attr) == getattr(wrapped, attr)
    assert inspect.signature(wrapped) == inspect.signature(function_factory)

    # check call output
    node = function_factory(3)
    assert isinstance(node, Node)
    assert node.name.endswith(name)
    assert node.function(5) == 4  # (5 + 3)/2
    assert node.default_factory() == default


def test_funfact_decorating_function_factory_without_parameters():
    @funfact
    def function_factory(a: int, b: int = 2) -> Callable[[int], float]:
        """function docstrings"""
        def function(n: int) -> float:
            return (n + a) / b
        return function
    common_case_check(function_factory, 'function_factory', None)


@pytest.mark.parametrize('name_param, name', [
    param({}, 'function_factory', id="no name"),
    param({'name': 'my_function'}, 'my_function', id="custom name"),
])
@pytest.mark.parametrize('default_params, default', [
    param({}, None, id="no default/default_factory"),
    param({'default': 0}, 0, id="default only"),
    param({'default_factory': list}, [], id="default_factory only"),
    param({'default_factory': list, 'default': 0}, [], id="default and default factory"),
])
def test_funfact_decorating_function_factory_with_parameters(name_param, name, default_params, default):
    @funfact(**name_param, **default_params)  # type: ignore
    def function_factory(a: int, b: int = 2) -> Callable[[int], float]:
        """function docstrings"""
        def function(n: int) -> float:
            return (n + a) / b
        return function
    common_case_check(function_factory, name, default)


def test_funfact_decorating_class_as_factory():
    @funfact
    class Factory:
        """class docstrings"""
        def __init__(self, a: int, b: int = 2):
            self.a = a
            self.b = b

        def __call__(self, n: int) -> float:
            return (n + self.a) / self.b
    common_case_check(Factory, "Factory", None)
