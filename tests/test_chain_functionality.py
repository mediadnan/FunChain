from pytest import mark

from fastchain import make, match, chainable  # noqa: used by eval()


@mark.parametrize("args, input, output", [
    ("increment", 1, 2),
    ("fail", 1, None),
    ("chainable(fail, default=0)", 1, 0),
    ("chainable(fail, default_factory=int)", 1, 0),
    ("increment, increment, increment", 1, 4),
    ("[increment, double]", 2, [3, 4]),
    ("{'a': increment, 'b': double}", 2, {'a': 3, 'b': 4}),
    ("match(increment, double)", [2, 3], [3, 6]),

])
def test_chain_call(increment, double, fail, args, input, output):
    chain = make(eval(args), log_failures=False, print_stats=False)
    assert chain(input) == output
