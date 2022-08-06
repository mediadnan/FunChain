from functools import partial, partialmethod
from typing import Any

import pytest

from fastchain._abc import ReporterBase  # noqa
from fastchain.chainables import *
from fastchain.chainables.base import optional


# basic functionality ---------------------------------------------------------------------------------------------------
chainable_name = "test_name"


@pytest.fixture
def chainable():
    class ChainableCopy(Chainable):
        def process(self, input, report): return True, input
    ChainableCopy.__name__ = ChainableCopy.__qualname__ = 'Chainable'
    return ChainableCopy(chainable_name)


@pytest.mark.parametrize("args, kwargs, expected_title", [
    ((), {}, chainable_name),
    (('root',), {}, f'root/{chainable_name}'),
    (('root', 'branch'), {}, f'root[branch]/{chainable_name}'),
    (('root', None), {}, f'root/{chainable_name}'),
    ((None, 'branch'), {}, chainable_name),
    ((), {'root': 'root'}, f'root/{chainable_name}'),
    ((), {'root': 'root', 'branch': 'branch'}, f'root[branch]/{chainable_name}'),
    (('root1/root2[b2]/root3', ), {'branch': 0},  f'root1/root2[b2]/root3[0]/{chainable_name}')
])
def test_chainable_base_set_title(chainable, args, kwargs, expected_title):
    assert chainable.name == chainable_name, "chainable name wasn't set correctly"
    assert chainable.title == chainable_name, "chainable default title=name wasn't set correctly"
    chainable.set_title(*args, **kwargs)
    assert chainable.name == chainable_name, "chainable name has been changed after calling .set_title()"
    assert chainable.title == expected_title, "chainable title wasn't updated correctly"


def test_chainable_repr(chainable):
    assert repr(chainable) == f'<chain-chainable: {chainable_name}>'


@pytest.mark.parametrize('func_str', ["OptionMap['?']", "optional"])
def test_optional_option(chainable, func_str):
    func = eval(func_str)
    assert chainable.optional is False, "chainable default optional=False wasn't set correctly"
    func(chainable)
    assert chainable.optional is True, "chainable.optional still False after applying option '?'"


def test_chainable_base_failure(chainable, test_reporter):
    inp, err = None, Exception()
    expected_failures = {chainable_name: dict(input=inp, error=err, fatal=True)}
    assert test_reporter.failures == {}, "reporter failures wasn't empty"
    chainable.failure(inp, err, test_reporter)
    assert test_reporter.failures == expected_failures, "chainable didn't register failure as expected"
    chainable.optional = True
    chainable.failure(inp, err, test_reporter)
    expected_failures[chainable_name]['fatal'] = False
    assert test_reporter.failures == expected_failures, "chainable registered failure as fatal even when optional"


# testing leaf nodes ----------------------------------------------------------------------------------------------------

def test_pass_call(test_reporter):
    inp = object()
    result = PASS.process(inp, test_reporter)
    assert result == (True, inp), "PASS result wasn't as expected"
    title = PASS.title
    PASS.set_title('root', 'branch')
    assert PASS.title == title, "pass title was changed, it should not."
    assert repr(PASS) == '<chain-pass>', "pass object wasn't represented as expected"


node_defaults = [
    pytest.param(dict(), None, id="default_default_value"),
    pytest.param(dict(default=None), None, id="explicit_default_value"),
    pytest.param(dict(default=""), "", id="custom_default_value('')"),
    pytest.param(dict(default_factory=list), [], id="custom_default_factory(list)"),
    pytest.param(dict(default=0, default_factory=str), "", id="default_factory_overrides_default(str > 0)"),
]


@pytest.mark.parametrize('name_kw, name', [
    (dict(), 'increment'),
    (dict(name='my_node'), 'my_node')
], ids=["default_name", "custom_name"])
@pytest.mark.parametrize('default_kw, default', node_defaults)
def test_node_chainable_creation(increment, name, default, name_kw: dict[str, Any], default_kw: dict[str, Any]):
    node = Node(increment, **name_kw, **default_kw)
    assert node.function is increment, "unexpected node function, wasn't identical"
    assert node.name == name, "unexpected node name"
    assert node.default_factory() == default, "unexpected node default"
    assert repr(node) == f'<chain-node: {name}>', "node object wasn't represented as expected"


@pytest.mark.parametrize('args, kwargs, exception_type, msg_contains', [
    ((), dict(), TypeError, r'.*'),
    ((None,), dict(), TypeError, r'\bmust be.*?callable\b'),
    ("increment", dict(name=5), TypeError, r"\bmust be.*?str\b"),
    ("increment", dict(name=''), ValueError, r"\bcannot be empty\b"),
    ("increment", dict(default_factory=""), TypeError, r'\bmust be.*?callable\b'),
], ids=[
    "no_arg_provided",
    "non_callable_as_function",
    "bad_name_type(5)",
    "empty_name",
    "bad_default_factory_value("")"
])
def test_node_validation(args, kwargs, exception_type, msg_contains, request):
    if isinstance(args, str):
        args = (request.getfixturevalue(args), )
    with pytest.raises(exception_type, match=msg_contains):
        Node(*args, **kwargs)


# bunch of functions expected by Node.get_qualname() ---# noqa
def func1(*args, **kwargs): pass                        # noqa
class Func:                                             # noqa
    def __call__(self, *args, **kwargs): pass           # noqa
class FuncHolder:                                       # noqa
    def func(self, *args, **kwargs): pass               # noqa
def funcfactory():                                      # noqa
    def func(*args, **kwargs): pass                     # noqa
    return func                                         # noqa
# ------------------------------------------------------# noqa


@pytest.mark.parametrize('function, name', [
    (func1, 'func1'),
    (Func(), 'Func_object'),
    (Func, 'Func'),
    (lambda x: x, '<lambda>'),
    (float, 'float'),
    (partial(func1, 1, 2, 3), 'func1'),
    (partial(partial(func1, 1, 2, 3), 4, 5, 6), 'func1'),
    (FuncHolder().func, 'FuncHolder.func'),
    (FuncHolder.func, 'FuncHolder.func'),
    (partialmethod(FuncHolder.func, 1, 2, 3), 'FuncHolder.func'),
    (funcfactory(), 'funcfactory.<locals>.func')
], ids=[
    'normal_function',
    'callable_object',
    'class',
    'lambda',
    'builtin_float',
    'partial',
    'partial_partial',
    'object_method',
    'class_method',
    'partial_class_method',
    'function_factory_function',
])
def test_node_get_qualname(function, name):
    assert Node.get_qualname(function) == name, f"qualname wasn't guessed for {function}"


def test_node_successful_processing_method(increment, test_reporter):
    node = Node(increment)
    assert not test_reporter.counter, "reporter's counter reg wasn't empty"
    assert not test_reporter.failures, "reporter's failures reg wasn't empty"
    assert node.process(5, test_reporter) == (True, 6), "the processing result wasn't as expected"
    assert test_reporter.counter[node] == [True], "node success wasn't registered"
    assert not test_reporter.failures, "reporter's failures reg was filled, it shouldn't"


@pytest.mark.parametrize('default_kw, default', node_defaults)
def test_node_unsuccessful_processing_method(fail, fake_error, test_reporter, default, default_kw: dict[str, Any]):
    node = Node(fail, **default_kw)
    assert not test_reporter.counter, "reporter's counter reg wasn't empty"
    assert not test_reporter.failures, "reporter's failures reg wasn't empty"
    assert node.process(5, test_reporter) == (False, default), "the processing result wasn't as expected"
    assert test_reporter.counter[node] == [False], "node fail wasn't registered"
    assert test_reporter.failures == {
        node.title: {
            'input': 5,
            'error': fake_error,
            'fatal': True
        }
    }, "reporter's failures reg still empty, it shouldn't"


# test node collections -------------------------------------------------------------------------------------------------

@pytest.fixture
def mock_collection():
    class TestCollection(Collection):
        def process(self, input, report: ReporterBase) -> tuple[bool, Any]: return True, input
    TestCollection.__name__ = 'collection'
    return TestCollection


@pytest.fixture
def chain_nodes_5(increment): return tuple(Node(increment, name=f'node-{i}') for i in range(5))
@pytest.fixture
def chain_node_inc(increment): return Node(increment)
@pytest.fixture
def chain_node_db(double): return Node(double)
@pytest.fixture
def chain_node_fail(fail): return Node(fail)
@pytest.fixture
def chain_node_optional_fail(fail): return optional(Node(fail))
@pytest.fixture
def chain_model(chain_node_inc, chain_node_db): return Model(increment=chain_node_inc, double=chain_node_db)
@pytest.fixture
def chain_group(chain_node_inc, chain_node_db): return Group(chain_node_inc, chain_node_db)


def test_collection_basic_creation(mock_collection, chain_nodes_5):
    coll = mock_collection(*chain_nodes_5)
    assert coll.name == 'collection'
    assert coll.members == chain_nodes_5
    assert coll.branches == ('0', '1', '2', '3', '4')


def test_collection_creation_with_branches(mock_collection, chain_nodes_5):
    with pytest.raises(TypeError):
        mock_collection((*chain_nodes_5, None))  # type: ignore
    keys = ('a', 'b', 'c', 'd', 'e')
    members = dict(zip(keys, chain_nodes_5))
    coll = mock_collection(**members)
    assert coll.members == chain_nodes_5
    assert coll.branches == ('a', 'b', 'c', 'd', 'e')


@pytest.mark.parametrize('args, coll_title, node_title', [
    ((), "collection", "collection[2]/node-2"),
    (('root', ), "root/collection", "root/collection[2]/node-2"),
    (('root', 'branch'), "root[branch]/collection", "root[branch]/collection[2]/node-2"),
], ids=[
    ".set_title()",
    ".set_title(root)",
    ".set_title(root, branch)"
])
def test_collection_set_title(mock_collection, chain_nodes_5, args, coll_title, node_title):
    nodes = chain_nodes_5[:3]
    coll = mock_collection(*nodes)
    assert coll.title == 'collection', "collection's title wasn't initially 'collection'"
    assert coll.members[-1].title == 'node-2', "2nd node member of collection's title wasn't initially 'node-2'"
    coll.set_title(*args)
    assert coll.title == coll_title, "collection's title wasn't updated successfully"
    assert coll.members[-1].title == node_title, "member's title wasn't updated successfully"


# test sequence
def test_sequence_successful_process(increment, double, test_reporter):
    nodes = Node(increment), Node(double)
    sequence = Sequence(*nodes)
    assert sequence.name == 'sequence'
    assert sequence.members == nodes
    assert sequence.process(4, test_reporter) == (True, 10)
    assert tuple(test_reporter.counter.values()) == ([True], [True])
    assert not test_reporter.failures


def test_sequence_unsuccessful_process_required(increment, fail, test_reporter):
    sequence = Sequence(Node(increment), Node(fail))
    assert sequence.process(4, test_reporter) == (False, None)
    assert tuple(test_reporter.counter.values()) == ([True], [False])
    assert len(test_reporter.failures) == 1


def test_sequence_unsuccessful_process_optional(increment, fail, test_reporter):
    sequence = Sequence(optional(Node(fail)), Node(increment))
    assert sequence.process(4, test_reporter) == (True, 5)
    assert tuple(test_reporter.counter.values()) == ([False], [True])
    assert len(test_reporter.failures) == 1


# test model
def test_model_creation(chain_node_inc, chain_node_db, chain_model):
    assert chain_model.members == (chain_node_inc, chain_node_db)
    assert chain_model.branches == ('increment', 'double')


def test_model_successful_process(chain_model, test_reporter):
    assert chain_model.process(3, test_reporter) == (True, {'increment': 4, 'double': 6})
    assert tuple(test_reporter.counter.values()) == ([True], [True])
    assert not test_reporter.failures


@pytest.mark.parametrize('fixt, result', [
    ("chain_node_fail", {'increment': 4, 'double': None}),
    ("chain_node_optional_fail", {'increment': 4}),
])
def test_model_partially_unsuccessful_process(chain_node_inc, fail, test_reporter, result, fixt, request):
    model = Model(increment=chain_node_inc, double=request.getfixturevalue(fixt))
    model.set_title()
    assert model.process(3, test_reporter) == (True, result)
    assert tuple(test_reporter.counter.values()) == ([True], [False])
    assert len(test_reporter.failures) == 1


def test_model_unsuccessful_process(fail, test_reporter):
    model = Model(increment=Node(fail), double=Node(fail))
    model.set_title()
    assert model.process(3, test_reporter) == (False, None)
    assert tuple(test_reporter.counter.values()) == ([False], [False])
    assert len(test_reporter.failures) == 2


# test group
def test_group_creation(chain_group, chain_node_db, chain_node_inc):
    assert chain_group.members == (chain_node_inc, chain_node_db)
    assert chain_group.branches == ('0', '1')


@pytest.mark.parametrize('fixt, result', [
    ("chain_node_fail", [4, None]),
    ("chain_node_optional_fail", [4]),
])
def test_group_partially_unsuccessful_process(chain_node_inc, fail, test_reporter, result, fixt, request):
    group = Group(chain_node_inc, request.getfixturevalue(fixt))
    group.set_title()
    assert group.process(3, test_reporter) == (True, result)
    assert tuple(test_reporter.counter.values()) == ([True], [False])
    assert len(test_reporter.failures) == 1


def test_group_unsuccessful_process(fail, test_reporter):
    group = Group(Node(fail), Node(fail))
    group.set_title()
    assert group.process(3, test_reporter) == (False, None)
    assert tuple(test_reporter.counter.values()) == ([False], [False])
    assert len(test_reporter.failures) == 2


# test match
# TODO test Match


# test option nodes -----------------------------------------------------------------------------------------------------

# TODO test options in general

# TODO test map option

