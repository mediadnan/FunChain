import pytest
from fastchain import *
from fastchain.chain import validate_name


# test name validation  -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('name', [None, 6, object()])
def test_type_validation(name: str):
    with pytest.raises(TypeError):
        validate_name(name)


@pytest.mark.parametrize('name', [
    '',
    'a',
    '-my_chain',
    '1chain',
    'my chain',
    'my.chain',
    'my/chain',
    'my:chain',
    'my[chain]',
    ' my_chain '
])
def test_forbidden_names(name):
    with pytest.raises(ValueError):
        validate_name(name)


@pytest.mark.parametrize('name', [
    'ca',
    'c1',
    'c_',
    'my-chain',
    'my_chain',
    'my_12chain',
    '__my_chain',
    '___my_chain',
])
def test_validate_name_allowed_names(name):
    assert validate_name(name) is name


# fixtures --------------------------------------------------------------------------------------------------------------

def fail(x): raise Exception(f"test_exception {x!r}")
def inc(x): return x + 1
def dbl(x): return x * 2


class CallableObj:
    def __call__(self, arg): return [arg]


# Chain functionalities -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("body, input, output", [
    # single function setups
    ("inc,", 3, 4,),
    ("lambda x: x - 1,", 4, 3),
    ("float,", "4", 4.0),
    ("round,", 4.143, 4),
    ("str,", 4, '4'),
    ("tuple,", 'abc', ('a', 'b', 'c')),
    ("CallableObj(),", 4, [4]),
    ("chainable(dbl),", 5, 10),
    ("chainable(lambda x, y: x + y, 2, name='add_two'),", 3, 5),

    # tuple of chainables setups
    ("inc, dbl", 6, 14),
    ("(((inc, dbl),),),", 6, 14),
    ("inc, dbl, inc", 2, 7),
    ("inc, (dbl, inc)", 2, 7),
    ("dbl, {'di': inc, 'dd': dbl}", 2, {"di": 5, "dd": 8}),
    ("dbl, [inc, dbl]", 2, [5, 8]),

    # list of chainables setups
    ("[inc],", 6, [7]),
    ("[inc, dbl],", 6, [7, 12]),
    ("[..., dbl],", 2, [2, 4]),
    ("[[inc, dbl], {'i': inc, 'd': dbl}, (inc, dbl)],", 2, [[3, 4], {'i': 3, 'd': 4}, 6]),

    # dict of chainables setups
    ("{'d': dbl},", 3, {'d': 6}),
    ("{'d': dbl, 'i': inc},", 3, {'d': 6, 'i': 4}),
    ("{'d': dbl, 'pass': ...},", 3, {'d': 6, 'pass': 3}),
    ("{'b1': (dbl, inc, [dbl, inc]), 'b2': inc},", 3, {'b1': [14, 8], 'b2': 4}),

    # match group
    ("match(inc, dbl), ", [2, 2], (3, 4)),
    ("dict.items, '*', match(str, (inc, dbl)), dict", {1: 1, 2: 2}, {'1': 4, '2': 6}),
])
def test_input_output(body, input, output):
    chain = Chain('test', *eval(body))
    res = chain(input)
    assert res == output
