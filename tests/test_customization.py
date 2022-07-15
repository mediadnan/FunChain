import functools
import pytest
import typing as tp
from fastchain.customization import chainable, funfact, PreNode
from fastchain.elements import ChainNode
from fastchain.reporter import Reporter

ROOT_NAME = "test"
POSITION = ()


def parse(pre_chainable: PreNode, **kwargs) -> ChainNode:
    """converts PreNode to chainNode - mocks the real parse function"""
    return pre_chainable.make(ROOT_NAME, POSITION, **kwargs)


# testing PreNode
@pytest.mark.parametrize("expr", (
        "PreNode()",
        "PreNode(None)",
        "PreNode(object())",
))
def test_pre_node_invalid_init(expr: str):
    """checks if raises for invalid input"""
    with pytest.raises(TypeError):
        eval(expr)


pre_node_scenarios = [
    pytest.param(
        parse(PreNode(lambda x: x)),
        "<lambda>",
        None,
        True,
        "process",
        id="defaults"
    ),
    pytest.param(
        parse(PreNode(lambda x: x, name="component", default_factory=list)),
        "component",
        [],
        True,
        "process",
        id="preset_name_default_factory"
    ),
    pytest.param(
        parse(PreNode(lambda x: x, name="component", default=0, optional=False, mode="*")),
        "component",
        0,
        False,
        "process_all",
        id="preset_values"
    ),
    pytest.param(
        parse(PreNode(lambda x: x), name="component", default=0, optional=False, mode="*"),
        "component",
        0,
        False,
        "process_all",
        id="make_values"
    ),
    pytest.param(
        parse(PreNode(lambda x: x, name="component", default=0, optional=False, mode="*"),
              name="my_comp", default=None, required=True, mode=None),
        "my_comp",
        None,
        True,
        "process",
        id="overriding_presets"
    ),
]


@pytest.mark.parametrize("node, name, default, required, call", pre_node_scenarios)
def test_pre_node_make(node: ChainNode, name: str, default: tp.Any, required: bool, call: str):
    """tests the stat after initialization"""
    assert node.root == "test", "failed to set the root"
    assert node.pos == (), "failed to set the position"
    assert node.name.endswith(name), "failed to set the name"
    assert node.default == default, "failed to set the expected default"
    assert node.optional == required, "failed to keep the default required"
    assert node._call == getattr(node, call), "failed to set the correct call mode"


def test_pre_node_keeps_call():
    """tests if the pre_node can still be called as function"""

    def func_(a: int) -> int:
        return a * 2

    pre_node = PreNode(func_)
    assert pre_node(5) == 10
    assert pre_node.func is func_


# testing chainable

def check_double_chainable(pre_object: PreNode) -> None:
    assert isinstance(pre_object, PreNode)
    node = parse(pre_object)
    assert node.name.rpartition('.')[2] == "double"
    assert node.function(3) == 6


def test_chainable_as_decorator():
    @chainable
    def double(a):
        return a * 2
    check_double_chainable(double)


def test_chainable_as_decorator_with_parenthesis():
    @chainable()
    def double(a):
        return a * 2
    check_double_chainable(double)


def test_chainable_as_decorator_with_parameters():
    @chainable(name="double", default=0)
    def func_(a):
        return a * 2
    check_double_chainable(func_)


def test_chainable_as_wrapper_with_function():
    def double(a):
        return a * 2
    check_double_chainable(chainable(double, name="double"))


def test_chainable_as_wrapper_with_lambda():
    check_double_chainable(chainable(lambda x: x * 2, name="double"))


def test_chainable_as_wrapper_with_partial():
    def multiply(a, b=1):
        return a * b
    check_double_chainable(chainable(functools.partial(multiply, b=2), name="double"))


def test_chainable_as_wrapper_with_internal_partial():
    def multiply(a, b=1):
        return a * b
    check_double_chainable(chainable(multiply, name="double", b=2))


# testing funfact
def test_funfact_empty():
    @funfact
    def double(b=2):
        def _double(a):
            return a * b
        return _double
    check_double_chainable(double())


def test_funfact_with_empty_parenthesis():
    @funfact()
    def double(b):
        def _double(a):
            return a * b
        return _double
    check_double_chainable(double(2))


def test_funfact_with_default():
    @funfact(name="double")
    def func(b=2):
        def _double(a):
            return a * b
        return _double
    check_double_chainable(func(2))


def test_funfact_with_name_override():
    @funfact(name="myfunc")
    def func(b=2):
        def _double(a):
            return a * b
        return _double
    check_double_chainable(func(2, name="double"))


def test_funfact_capture_special_kwargs():
    @funfact
    def greeting(time_of_day: tp.Literal['morning', 'evening', 'afternoon'] = 'morning', name: str | None = None):
        def _greeting(value: tp.Any) -> str:
            return f"good {time_of_day} {name or 'person'}, you passed {value!r}"
        return _greeting
    node = parse(greeting("evening", name="adnan"))
    assert node.name == "adnan"
    assert node.function(2) == "good evening adnan, you passed 2"


def test_funfact_map_mode():
    @funfact
    def multiply(second):
        def _multiply(first):
            return first * second
        return _multiply
    node = parse(multiply(3, name="triple", mode="*"))
    reporter = Reporter([node])
    success, result = node([3, 4, 5], reporter)
    report = reporter.report()
    assert success
    assert list(result) == [9, 12, 15]
    assert report['success_rate'] == 1.0
    assert report['succeeded'] == 3
