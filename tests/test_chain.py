import pytest
from typing import Type, Any
from fastchain import Chain, ChainMaker, chainable
from fastchain.chainables import Node, Chainable, Sequence, Group, Model, Match


def fail(x): raise Exception(f"test_exception {x!r}")
def inc(x): return x + 1
def dbl(x): return x * 2


class CallableObj:
    def __call__(self, arg): return [arg]


# Chain functionalities -------------------------------------------------------------------------------------------------

# SETUPS are tuples with following structure
#   0: param id
#   1: chain body
#   2: parsed type
#   3: input arg, output result
SETUPS: tuple[tuple[str, tuple, Type[Chainable], tuple[Any, Any]], ...] = (
    # single function setups
    ("normal_function", (inc,), Node, (3, 4),),
    ("lambda_function", (lambda x: x - 1,), Node, (4, 3), ),
    ("builtin_float", (float,), Node, ("4", 4.0), ),
    ("builtin_round", (round,), Node, (4.143, 4), ),
    ("builtin_str", (str,), Node, (4, '4'), ),
    ("builtin_tuple", (tuple,), Node, ('abc', ('a', 'b', 'c')), ),
    ("callable_object_as_function", (CallableObj(),), Node, (4, [4]), ),
    ("function_decorated_with_chainable", (chainable(dbl),), Node, (5, 10)),
    ("function_decorated_with_chainable_partial", (chainable(lambda x, y: x + y, 2, name='add_two'), ), Node, (3, 5)),

    # tuple of chainables setups
    ("sequence_of_two_functions", (inc, dbl), Sequence, (6, 14)),
    ("sequence_of_two_functions_with_explicit_tuple", ((((inc, dbl),),),), Sequence, (6, 14)),
    ("sequence_of_three_functions", (inc, dbl, inc), Sequence, (2, 7)),
    ("sequence_of_function_and_tuple", (inc, (dbl, inc)), Sequence, (2, 7)),
    ("sequence_of_function_and_dict", (dbl, {"di": inc, "dd": dbl}), Sequence, (2, {"di": 5, "dd": 8})),
    ("sequence_of_function_and_list", (dbl, [inc, dbl]), Sequence, (2, [5, 8])),

    # list of chainables setups
    ("group_of_single_functions", ([inc],), Group, (6, [7])),
    ("group_of_two_functions", ([inc, dbl],), Group, (6, [7, 12])),
    ("group_with_pass_branch", ([..., dbl],), Group, (2, [2, 4])),
    ("group_with_nested_branches", ([[inc, dbl], {"i": inc, "d": dbl}, (inc, dbl)],), Group, (2, [[3, 4], {'i': 3, 'd': 4}, 6])),  # noqa

    # dict of chainables setups
    ("model_with_single_function", ({"d": dbl},), Model, (3, {'d': 6})),
    ("model_with_two_function", ({"d": dbl, "i": inc},), Model, (3, {'d': 6, 'i': 4})),
    ("model_with_single_function", ({"d": dbl, "pass": ...},), Model, (3, {'d': 6, 'pass': 3})),
    ("model_with_nested_branches", ({"b1": (dbl, inc, [dbl, inc]), "b2": inc},), Model, (3, {'b1': [14, 8], 'b2': 4})),  # noqa

    # match group
    ("match_group", (':', [inc, dbl]), Match, ([2, 2], [3, 4])),
    ("match_nested_branches", (':', [(inc, dbl), [dbl, inc]]), Match, ([2, 3], [6, [6, 4]]))
)

ids, structures, types, inp_out, = zip(*SETUPS)


@pytest.mark.parametrize("body, typ", zip(structures, types), ids=ids)
def test_parsed_type(body, typ):
    assert isinstance(Chain.parse(body), typ), f'{body!r} is not parsed to the expected type {typ!r}'


@pytest.mark.parametrize("body, input_output", zip(structures, inp_out), ids=ids)
def test_input_output(body, input_output):
    chain = Chain('test', *body)
    inp, out = input_output
    res = chain(inp)
    assert res == out, f"unexpected output from {body!r}, expected {out!r} got {res!r}"


@pytest.mark.parametrize("node, output", (
        (inc, [3, 4]),
        ((inc, dbl), [6, 8]),
        ([inc, dbl], [[3, 4], [4, 6]]),
        ({'di': (dbl, inc), 'id': (inc, dbl)}, [{'di': 5, 'id': 6}, {'di': 7, 'id': 8}]),
))
def test_iter_option(node, output):
    input = [2, 3]
    chain = Chain("test", '*', node, list)
    assert chain(input) == output
