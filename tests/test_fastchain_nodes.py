from pytest import mark
from asyncio import iscoroutine, run
from funchain import core, chain, loop  # noqa (used in eval)


# fixtures

def increment(number: int) -> int:
    return number + 1


async def a_increment(number: int) -> int:
    return number + 1


def double(number: int) -> int:
    return number * 2


class Add:  # OOP style factory
    def __init__(self, number: int):
        self.number = number

    def __call__(self, number: int) -> int:
        return self.number + number


def add(number: int):   # functional style factory
    def _add(num: int) -> int:
        return number + num
    return _add


test_cases = [
    # Testing simple nodes creation and execution
    ('chain()', 5, 5),
    ('chain(increment)', 3, 4),
    ('chain(Add(1))', 3, 4),
    ('chain(add(1))', 3, 4),
    ('chain(increment, double)', 3, 8),
    ('chain(increment) + double', 3, 8),
    ('chain(increment, increment, increment, increment, increment)', 2, 2 + 5),
    ('chain(double) * chain(increment)', [3], [4, 4]),
    ('chain(double, loop(increment))', [3], [4, 4]),
    ('chain(loop(increment), sum)', [3, 4], 9),
    ('chain(loop((increment, double)), sum)', [3, 4], 18),
    ('chain({"double": double, "increment": increment})', 7, {'double': 14, 'increment': 8}),
    ('chain([increment, double])', 7, [8, 14]),
    ('chain({"double": double, "increment": chain(increment, increment)})', 7, {'double': 14, 'increment': 9}),
    ('chain([double, chain(increment, increment)])', 7, [14, 9]),

    # Testing async nodes creation and execution
    ('chain(a_increment)', 3, 4),
    ('chain(a_increment, a_increment)', 3, 5),
    ('chain(increment, a_increment)', 3, 5),
    ('chain(increment) + chain(a_increment)', 3, 5),
    ('chain(a_increment) + chain(increment)', 3, 5),
    ('loop(a_increment)', [3, 4, 5], (4, 5, 6)),
    ('chain(loop(a_increment), sum)', [3, 4, 5], 15),
    ('chain({"ai": a_increment, "i": increment})', 7, {'ai': 8, 'i': 8}),
    ('chain([a_increment, increment])', 7, [8, 8]),
    ('chain({"ai": a_increment, "ai2": a_increment})', 7, {'ai': 8, 'ai2': 8}),
    ('chain([a_increment, a_increment])', 7, [8, 8]),
]


# tests
@mark.parametrize('src, inp, out', test_cases, ids=[i[0] for i in test_cases])
def test_node_function(src, inp, out, reporter):
    function = eval(src)
    result = function(inp, reporter)
    if iscoroutine(result):
        result = run(result)
    assert result == out, "node outputted an unexpected value"
