import itertools
from functools import partial, partialmethod
from typing import Type, Any

import pytest
from pytest import param

from fastchain._abc import ReporterBase  # noqa
from fastchain.chainables import *
from fastchain.chainables.options import *


# basic functionality ---------------------------------------------------------------------------------------------------
chainable_name = "test_name"


@pytest.fixture
def chainable():
    class ChainableCopy(Chainable):
        def __len__(self): return 1
        def process(self, input, report): return True, input
    ChainableCopy.__name__ = ChainableCopy.__qualname__ = 'Chainable'
    return ChainableCopy(chainable_name)


@pytest.mark.parametrize('params, expected_default_name', [
    param({}, 'chainable_sub_class', id="no keywords provided"),
    param({'type_name': None}, 'chainable_sub_class', id="explicit None as type_name"),
    param({'type_name': 'my_custom_name'}, 'my_custom_name', id="custom type_name"),
])
def test_chainable_default_name(params: dict[str, Any], expected_default_name: str):
    class ChainableSubClass(Chainable, **params): pass  # noqa
    assert ChainableSubClass.NAME == expected_default_name


@pytest.mark.parametrize(
    "args, kwargs, expected_title", [
        ((), {}, chainable_name),
        (('root',), {}, f'root/{chainable_name}'),
        (('root', 'branch'), {}, f'root[branch]/{chainable_name}'),
        (('root', None), {}, f'root/{chainable_name}'),
        ((None, 'branch'), {}, chainable_name),
        ((), {'root': 'root'}, f'root/{chainable_name}'),
        ((), {'root': 'root', 'branch': 'branch'}, f'root[branch]/{chainable_name}'),
        (('root1/root2[b2]/root3',), {'branch': 0}, f'root1/root2[b2]/root3[0]/{chainable_name}')
    ]
)
def test_chainable_base_set_title(chainable, args, kwargs, expected_title):
    assert chainable.name == chainable_name, "chainable name wasn't set correctly"
    assert chainable.title == chainable_name, "chainable default coll_title=name wasn't set correctly"
    chainable.set_title(*args, **kwargs)
    assert chainable.name == chainable_name, "chainable name has been changed after calling .set_title()"
    assert chainable.title == expected_title, "chainable coll_title wasn't updated correctly"


def test_chainable_repr(chainable):
    assert repr(chainable) == f'<ChainChainable: {chainable_name}>'


@pytest.mark.parametrize('func_str', ["OptionMap['?']", "optional"])
def test_optional_option(chainable, func_str):
    func = eval(func_str)
    assert chainable.optional is False, "chainable default optional=False wasn't set correctly"
    func(chainable)
    assert chainable.optional is True, "chainable.optional still False after applying option '?'"


def test_chainable_base_failure(chainable, test_reporter):
    inp, err = None, Exception()
    expected_failures = {chainable_name: dict(source=chainable.title, input=inp, error=err, fatal=True)}
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
    assert PASS.title == title, "pass coll_title was changed, it should not."
    assert repr(PASS) == '<chain-pass>', "pass object wasn't represented as expected"
    assert len(PASS) == 0, "PASS has no size"


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
    assert repr(node) == f'<ChainNode: {name}>', "node object wasn't represented as expected"
    assert len(node) == 1


@pytest.mark.parametrize(
    'args, kwargs, exception_type, msg_contains', [
        ((), dict(), TypeError, r'.*'),
        ((None,), dict(), TypeError, r'must be.*?callable\b'),
        ("increment", dict(name=5), TypeError, r"must be.*?str\b"),
        ("increment", dict(name=''), ValueError, r"cannot be empty\b"),
        ("increment", dict(default_factory=""), TypeError, r'must be.*?callable\b'),
    ], ids=[
        "no_arg_provided",
        "non_callable_as_function",
        "bad_name_type(5)",
        "empty_name",
        "bad_default_factory_value("")"
    ]
)
def test_node_validation(args, kwargs, exception_type, msg_contains, request):
    if isinstance(args, str):
        args = (request.getfixturevalue(args),)
    with pytest.raises(exception_type, match=msg_contains):
        Node(*args, **kwargs)


# bunch of functions expected by Node.get_qualname() ---
def func1(*_, **__): pass


class Func:
    def __call__(self, *_, **__): pass


class FuncHolder:
    def func(self, *_, **__): pass


def funcfactory():
    def func(*_, **__): pass
    return func
# ------------------------------------------------------


@pytest.mark.parametrize(
    'function, name', [
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
    ]
)
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
            'source': node.title,
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


CollectionTypes = ["Sequence", "ListModel", "DictModel", "Match"]
collection_lower_names = ["sequence", "list_model", "dict_model", "match"]


@pytest.mark.parametrize('col_type, col_name', zip(CollectionTypes, collection_lower_names, strict=True))
def test_collection_basic_creation(col_type, col_name, chain_nodes_5):
    coll = eval(col_type)(*chain_nodes_5)
    assert coll.name == col_name
    assert coll.members == chain_nodes_5
    assert coll.branches == ('0', '1', '2', '3', '4')
    assert len(coll) == 5


def test_collection_creation_with_branches(mock_collection, chain_nodes_5):
    keys = ('a', 'b', 'c', 'd', 'e')
    members = dict(zip(keys, chain_nodes_5))
    coll = mock_collection(**members)
    assert coll.members == chain_nodes_5
    assert coll.branches == ('a', 'b', 'c', 'd', 'e')


@pytest.mark.parametrize('source, error', [
    ("cls()", ValueError),
    ("cls(Node(increment), Node(increment), None)", TypeError),
    ("cls(Node(increment), increment=Node(increment))", ValueError),
], ids=[
    "passing no members",
    "non-chainable members",
    "mixing positional and keyword members",
])
@pytest.mark.parametrize('collection', CollectionTypes)
def test_collection_validation(collection, source, error: Type[Exception], increment):
    with pytest.raises(error):
        eval(source.replace('cls', collection))


@pytest.mark.parametrize('collection', CollectionTypes)
def test_collection_refuse_mixing_positional_and_keyword_members(increment, collection):
    pytest.raises(ValueError, eval(collection), Node(increment), increment=Node(increment))


@pytest.mark.parametrize('collection, coll_title', zip(CollectionTypes, collection_lower_names, strict=True))
@pytest.mark.parametrize(
    'args, exp_coll_title, exp_node_title', [
        ((), "{coll_title}", "{coll_title}[{index}]/{node_title}"),
        (('root',), "root/{coll_title}", "root/{coll_title}[{index}]/{node_title}"),
        (('root', 'branch'), "root[branch]/{coll_title}", "root[branch]/{coll_title}[{index}]/{node_title}"),
    ], ids=[
        "set_title()",
        "set_title(root)",
        "set_title(root, branch)"
    ]
)
def test_collection_set_title(collection, coll_title, args, exp_coll_title, exp_node_title):
    node_title = "my_node_6345"
    index = 1
    def func(_): pass
    coll = eval(collection)(Node(func), Node(func, name=node_title))
    assert coll.title == coll_title
    assert coll.members[index].title == node_title
    coll.set_title(*args)
    assert coll.title == exp_coll_title.format(coll_title=coll_title, index=index, node_title=node_title)
    assert coll.members[index].title == exp_node_title.format(coll_title=coll_title, index=index, node_title=node_title)


COLL_SRC = [
    "Sequence(chain_node_inc, chain_node_db)",
    "DictModel(increment=chain_node_inc, double=chain_node_db)",
    "ListModel(chain_node_inc, chain_node_db)",
    "Match(chain_node_inc, chain_node_db)",
]
COLL_TYPES = [Sequence, DictModel, ListModel, Match]
BRANCHES_NAMES = [('0', '1'), ('increment', 'double')]


@pytest.mark.parametrize('source_coll, coll_type, bn', zip(COLL_SRC, COLL_TYPES, (0, 1, 0, 0)))
def test_collection_creation(source_coll, coll_type, chain_node_inc, chain_node_db, bn):
    coll = eval(source_coll)
    assert isinstance(coll, coll_type)
    assert coll.members == (chain_node_inc, chain_node_db)
    assert coll.branches == BRANCHES_NAMES[bn]


@pytest.mark.parametrize('source_coll, expected_default', [
    param("Sequence(Node(increment, default=0), Node(increment, default=1))", 1, id="sequence of two required nodes"),
    param("Sequence(Node(increment, default=0), optional(Node(increment, default=1)))", 0, id="sequence of a required and optional node"),  # noqa

    param("Match(Node(increment, default=0), Node(increment, default=1))", (0, 1), id="Match of two required nodes"),
    param("Match(Node(increment, default=0), optional(Node(increment, default=1)))", (0, 1), id="Match of a required and optional nodes"),  # noqa

    param("DictModel(Node(increment, default=0), Node(increment, default=1))", {'0': 0, '1': 1}, id="DictModel of two required nodes"),  # noqa
    param("DictModel(Node(increment, default=0), optional(Node(increment, default=1)))", {'0': 0}, id="DictModel of a required and optional nodes"),  # noqa

    param("ListModel(Node(increment, default=0), Node(increment, default=1))", [0, 1], id="ListModel of two required nodes"),  # noqa
    param("ListModel(Node(increment, default=0), optional(Node(increment, default=1)))", [0], id="ListModel of a required and optional nodes"),  # noqa
])
def test_collection_defaults(source_coll: str, expected_default, increment):
    assert eval(source_coll).default_factory() == expected_default


COLL_SETUPS = {
    'ID': "Node(increment), Node(double)",
    'IF': "Node(increment), Node(fail)",
    'If': "Node(increment), optional(Node(fail))",
    'FF': "Node(fail), Node(fail)",
    'ff': "optional(Node(fail)), optional(Node(fail))"
}

GIVEN_INPUT = {
    "Sequence": 4,
    "DictModel": 4,
    "ListModel": 4,
    "Match": [4, 4],
}

EXPECTED_RESULTS = {
    "Sequence": {
        'ID': (True, 10),
        'IF': (False, None),
        'If': (True, 5),
        'FF': (False, None),
        'ff': (False, 4),
    },
    "DictModel": {
        'ID': (True, {'0': 5, '1': 8}),
        'IF': (False, {'0': 5, '1': None}),
        'If': (True, {'0': 5}),
        'FF': (False, {'0': None, '1': None}),
        'ff': (False, {}),
    },
    "ListModel": {
        'ID': (True, [5, 8]),
        'IF': (False, [5, None]),
        'If': (True, [5]),
        'FF': (False, [None, None]),
        'ff': (False, []),
    },
    "Match": {
        'ID': (True, (5, 8)),
        'IF': (False, (5, None)),
        'If': (False, (5, None)),
        'FF': (False, (None, None)),
        'ff': (False, (None, None)),
    }
}


def generate_collection_cases():
    for coll_type, input in GIVEN_INPUT.items():
        for setup_name, setup in COLL_SETUPS.items():
            try:
                expected_result = EXPECTED_RESULTS[coll_type][setup_name]
            except KeyError:
                # In case collection type is not specified or its setup is not specified
                continue
            source = f'{coll_type}({setup})'
            yield pytest.param(source, input, expected_result, id=f"{coll_type}[{setup_name}]({input!r})")


@pytest.mark.parametrize('source, input, result', generate_collection_cases())
def test_collection_failure_combination(
        source: str,
        test_reporter,
        increment,
        double,
        fail,
        input,
        result,
):
    coll: Collection = eval(source)
    coll.set_title()
    assert coll.process(input, test_reporter) == result


@pytest.mark.parametrize('input, Error', [
    ((1, ), ValueError),
    ((1, 2, 3), ValueError),
    (None, TypeError),
], ids=[
    "items less than members",
    "items more than members",
    "non_iterable object",
])
def test_match_specific_failures(increment, double, test_reporter, input, Error: Type[Exception]):
    chain_match = Match(Node(increment), Node(double))
    success, result = chain_match.process(input, test_reporter)
    assert not success
    assert result == (None, None)
    assert True not in itertools.chain(*test_reporter.counter.values())
    registered_error = test_reporter.failures[chain_match.title]['error']
    assert isinstance(registered_error, Error)


# test options ----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('option_symbol', OptionMap.keys())
def test_applying_option(option_symbol: str, chainable):
    chainable_ = chainable
    assert chainable_ is OptionMap[option_symbol](chainable)


def test_for_each_option(chain_node_inc, test_reporter):
    node = for_each(chain_node_inc)
    success, result = node.process((2, 5, 8), test_reporter)
    assert success
    assert tuple(result) == (3, 6, 9)


def test_for_each_option_failure(chain_node_inc, test_reporter):
    node = for_each(chain_node_inc)
    success, result = node.process(3, test_reporter)
    assert not success
    assert result == ()
    assert isinstance(test_reporter.failures[node.title]['error'], TypeError)
