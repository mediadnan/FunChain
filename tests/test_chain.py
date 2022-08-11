import pytest
from typing import Type, Any
from fastchain import Chain, ChainMaker, chainable
from fastchain.chainables import Node, Chainable, Sequence, ListModel, DictModel, Match


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
#   3: input arg, result output
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

    ("sequence_of_two_functions", (inc, dbl), Sequence, (6, 14)),
    ("sequence_of_two_functions_with_explicit_tuple", ((((inc, dbl),),),), Sequence, (6, 14)),
    ("sequence_of_three_functions", (inc, dbl, inc), Sequence, (2, 7)),
    ("sequence_of_function_and_tuple", (inc, (dbl, inc)), Sequence, (2, 7)),
    ("sequence_of_function_and_dict", (dbl, {"di": inc, "dd": dbl}), Sequence, (2, {"di": 5, "dd": 8})),
    ("sequence_of_function_and_list", (dbl, [inc, dbl]), Sequence, (2, [5, 8])),

    ("group_of_single_functions", ([inc],), ListModel, (6, [7])),
    ("group_of_two_functions", ([inc, dbl],), ListModel, (6, [7, 12])),
    ("group_with_pass_branch", ([..., dbl],), ListModel, (2, [2, 4])),
    ("group_with_nested_branches", ([[inc, dbl], {"i": inc, "d": dbl}, (inc, dbl)],), ListModel, (2, [[3, 4], {'i': 3, 'd': 4}, 6])),  # noqa

    ("model_with_single_function", ({"d": dbl},), DictModel, (3, {'d': 6})),
    ("model_with_two_function", ({"d": dbl, "i": inc},), DictModel, (3, {'d': 6, 'i': 4})),
    ("model_with_single_function", ({"d": dbl, "pass": ...},), DictModel, (3, {'d': 6, 'pass': 3})),
    ("model_with_nested_branches", ({"b1": (dbl, inc, [dbl, inc]), "b2": inc},), DictModel, (3, {'b1': [14, 8], 'b2': 4})),  # noqa

    ("match_group", (':', [inc, dbl]), Match, ([2, 2], [3, 4])),
    ("match_nested_branches", (':', [(inc, dbl), [dbl, inc]]), Match, ([2, 3], [6, [6, 4]]))
)

ids, structures, types, inp_out, = zip(*SETUPS)


@pytest.mark.parametrize("body, input, output", [
    # single function setups
    pytest.param("(inc,)", 3, 4),    # normal_function
    pytest.param("(lambda x: x - 1,)", 4, 3),  # lambda_function
    pytest.param("(float,)", "4", 4.0),  # builtin_float
    pytest.param("(round,)", 4.143, 4),  # builtin_round
    pytest.param("(str,)", 4, '4'),    # builtin_str
    pytest.param("(tuple,)", 'abc', ('a', 'b', 'c')),    # builtin_tuple
    pytest.param("(CallableObj(),)", 4, [4]),  # callable_object_as_function
    pytest.param("(chainable(dbl),)", 5, 10),    # function_decorated_with_chainable
    pytest.param("(chainable(lambda x, y: x + y, 2, name='add_two'), )", 3, 5),  # decorated_with_chainable_partial
    # tuple of chainables setups
    pytest.param("(inc, dbl)", 6, 14),   # sequence_of_two_functions
    pytest.param("((((inc, dbl),),),)", 6, 14),  # sequence_of_two_functions_with_explicit_tuple
    pytest.param("(inc, dbl, inc)", 2, 7),     # sequence_of_three_functions
    pytest.param("(inc, (dbl, inc))", 2, 7),    # sequence_of_function_and_tuple
    pytest.param("(dbl, {'di': inc, 'dd': dbl})", 2, {"di": 5, "dd": 8}),    # sequence_of_function_and_dict
    pytest.param("(dbl, [inc, dbl])", 2, [5, 8]),    # sequence_of_function_and_list
    # list of chainables setups
    pytest.param("([inc],)", 6, [7]),  # group_of_single_functions
    pytest.param("([inc, dbl],)", 6, [7, 12]),  # group_of_two_functions
    pytest.param("([..., dbl],)", 2, [2, 4]),  # group_with_pass_branch
    pytest.param("([[inc, dbl], {'i': inc, 'd': dbl}, (inc, dbl)],)", 2, [[3, 4], {'i': 3, 'd': 4}, 6]),  # group_with_nested_branches
    # dict of chainables setups
    pytest.param("({'d': dbl},)", 3, {'d': 6}),  # model_with_single_function
    pytest.param("({'d': dbl, 'i': inc},)", 3, {'d': 6, 'i': 4}),  # model_with_two_function
    pytest.param("({'d': dbl, 'pass': ...},)", 3, {'d': 6, 'pass': 3}),  # model_with_single_function
    pytest.param("({'b1': (dbl, inc, [dbl, inc]), 'b2': inc},)", 3, {'b1': [14, 8], 'b2': 4}),  # model_with_nested_branches
    # match group
    pytest.param("(':', [inc, dbl])", [2, 2], [3, 4]),  # match_group
    # pytest.param("(':', [inc, dbl])", ([2, 2], [3, 4])),  # match_nested_branches
])
def test_input_output(body, input, output):
    chain = Chain('test', *eval(body))
    res = chain(input)
    assert res == output


# @pytest.mark.parametrize("node, result", (
#         (inc, [3, 4]),
#         ((inc, dbl), [6, 8]),
#         ([inc, dbl], [[3, 4], [4, 6]]),
#         ({'di': (dbl, inc), 'id': (inc, dbl)}, [{'di': 5, 'id': 6}, {'di': 7, 'id': 8}]),
# ))
# def test_iter_option(node, output):
#     input = [2, 3]
#     chain = Chain("test", '*', node, list)
#     assert chain(input) == output
