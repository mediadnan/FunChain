import itertools
import pytest
from pytest import param

from fastchain.chainables import *
from fastchain.chainables.options import *
from fastchain.factory import *
from fastchain.monitoring import *


def func(_): pass


# test reporter maker

SETUP_CASES = [
    "(func,)",
    "('?', func)",
    "(func, func)",
    "(func, '?', func)",
    "('?', func, '?', func)",
    "(func, '?', (func, func))",
    "match(func, (func, '?', func))",
    "[func, ('?', func)]",
    "[func, ('?', (func, func))]",
    "{'required': func, 'optional': ('?', func)}",
]
REQUIRED_NODES = [1, 0, 2, 1, 0, 1, 2, 1, 1, 1]
TOTAL_NODES = [1, 1, 2, 2, 2, 3, 3, 2, 3, 2]
MINIMUM_RATE = ['1', '0', '1', '1/2', '0', '1/3', '2/3', '1/2', '1/3', '1/2']


@pytest.mark.parametrize('setup, required, total', zip(SETUP_CASES, REQUIRED_NODES, TOTAL_NODES), ids=repr)
def test_get_nodes(setup, required, total):
    res = ReporterMaker.get_nodes(parse(eval(setup)))  # type: ignore[parse]
    assert all(isinstance(c, Node) for c in res)
    assert operator.countOf(res.values(), True) == required
    assert len(res) == total


@pytest.mark.parametrize('handlers', HandlersCombination, ids=repr)
@pytest.mark.parametrize('setup, required_nodes', zip(SETUP_CASES, MINIMUM_RATE), ids=repr)
def test_reporter_maker(setup, minimum_rate, handlers):
    chainable_object = parse(eval(setup))
    rm = ReporterMaker('test', chainable_object, handlers)
    reporter = rm()
    assert isinstance(reporter, Reporter)
    for handler, handler_type in zip(rm.failure_handlers, handlers, strict=True):
        assert isinstance(handler, handler_type)
        assert handler.owner == 'test'
    assert reporter.failure_handlers is rm.failure_handlers
    assert rm.components == frozenset(ReporterMaker.get_nodes(chainable_object))
    assert rm.required_nodes == eval(minimum_rate)
    assert reporter.required_nodes == rm.required_nodes


@pytest.mark.parametrize('args_source, Error, msg', [
    ("None, []", TypeError, "chainable must be an instance of Chainable subclass"),
    ("object(), []", TypeError, "chainable must be an instance of Chainable subclass"),
    ("parse((func, func)), [None]", TypeError, "handlers must be a list of fastchain.monitoring.FailureHandler subclasses"),  # noqa
    ("parse((func, func)), [float]", TypeError, "handlers must be a list of fastchain.monitoring.FailureHandler subclasses"),  # noqa
], ids=repr)
def test_reporter_maker_validation(args_source, Error, msg):
    with pytest.raises(Error, match=msg):
        ReporterMaker('test', *eval(args_source))


# test reporter
@pytest.fixture
def nodes(): return tuple(Node(func, name=f'node{i+1}') for i in range(4))
@pytest.fixture
def reporter(nodes): return Reporter(frozenset(nodes), 1, [])


def test_reporter_creation(nodes):
    reporter = Reporter(frozenset(nodes), 1, [])
    assert reporter.counter == {node: [] for node in nodes}
    assert reporter.required_nodes == 1
    assert reporter._failures == []
    assert reporter.failure_handlers == []


@pytest.mark.parametrize('combination, rate, successes, failures, missed', [
    param([[True], [True], [True], [True]], 4/4, 4, 0, 0, id="single success marks"),
    param([[True, True, True, True], [True], [True], [True, True]], 8/8, 8, 0, 0, id="multiple success marks"),
    param([[False], [False], [False], [False]], 0/4, 0, 4, 0, id="single fail marks"),
    param([[False, False], [False], [False], [False, False]], 0/6, 0, 6, 0, id="multiple fail marks"),
    param([[True], [True], [False], [False]], 2/4, 2, 2, 0, id="single hybrid marks"),
    param([[True, True, False], [True], [True, False], [False]], (2/3+1+1/2+0)/4, 4, 3, 0, id="multiple hybrid marks"),
    param([[True], [True], [False], []], 2/4, 2, 1, 1, id="single last one missed"),
    param([[True, True], [True, False], [], []], (1+1/2+0+0)/4, 3, 1, 2, id="multiple last two missed"),
])
def test_reporter_statistics(reporter, nodes, combination: list[list[bool]], rate: float, successes, failures, missed):
    for node, states in zip(nodes, combination):
        for state in states:
            reporter(node, state)
    statistics = reporter.statistics()
    assert statistics['success_rate'] == round(rate, 4)
    assert statistics['successful_node_operations'] == successes
    assert statistics['failed_node_operations'] == failures
    assert statistics['missed_nodes'] == missed


def test_report_failure(nodes):
    failure_handler = _FailureHandler_('test')
    reporter = Reporter(frozenset(nodes), 1, [failure_handler])
    error = ValueError('test')
    assert not failure_handler.called
    reporter.register_failure('test', None, error, fatal=True)
    assert failure_handler.called
    assert reporter._failures == [FailureDetails(source="test", input=None, error=error, fatal=True)]


@pytest.mark.parametrize('reps', (0, 1, 2, 3), ids=repr)
@pytest.mark.parametrize('source, input, error, fatal', itertools.product(('test',),
                                                                          (None, ''),
                                                                          (ValueError('test'), TypeError('test')),
                                                                          (True, False)), ids=repr)
def test_report_multiple_failures(reporter, source: str, input, error: Exception, fatal: bool, reps: int):
    for _ in range(reps):
        reporter.register_failure(source, input, error, fatal)
    assert reporter.failures == [FailureDetails(source=source, input=input, error=error, fatal=fatal)] * reps


@pytest.mark.parametrize('success_stat', (True, False))
def test_marking_unregistered_node(reporter, success_stat):
    node = Node(func)
    with pytest.warns(UserWarning, match=f'unregistered node {node!r} ignored'):
        reporter(node, success_stat)
