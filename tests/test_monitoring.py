# import itertools
# import pytest
# from pytest import param
#
# from fastchain.chainables import *
# from fastchain.chainables.options import *
# from fastchain.factory import *
# from fastchain.monitoring import *
#
#
# def func(_): pass
#
#
# # test reporter maker
# SETUP_CASES = [
#     ("(func,)", 1, 1),
#     ("('?', func)", 0, 1),
#     ("(func, func)", 2, 2),
#     ("(func, '?', func)", 1, 2),
#     ("('?', func, '?', func)", 0, 2),
#     ("(func, '?', (func, func))", 1, 3),
#     ("match(func, (func, '?', func))", 2, 3),
#     ("[func, ('?', func)]", 1, 2),
#     ("[func, ('?', (func, func))]", 1, 3),
#     ("{'required': func, 'optional': ('?', func)}", 1, 2),
# ]
# SETUPS, REQUIRED_NODES, TOTAL_NODES = zip(*SETUP_CASES)
#
#
# @pytest.mark.parametrize('setup, required, total', SETUP_CASES, ids=repr)
# def test_get_nodes(setup, required, total):
#     res = ReporterMaker.get_nodes(parse(eval(setup)))
#     assert all(isinstance(c, Node) for c in res)
#     assert operator.countOf(res.values(), True) == required
#     assert len(res) == total
#
#
# @pytest.mark.parametrize('setup, required_nodes', zip(SETUPS, REQUIRED_NODES), ids=repr)
# def test_reporter_maker(setup, required_nodes):
#     chainable_object = parse(eval(setup))
#     rm = ReporterMaker(chainable_object)
#     reporter = rm()
#     assert isinstance(reporter, Reporter)
#     assert rm.components == frozenset(ReporterMaker.get_nodes(chainable_object))
#     assert rm.required_nodes == required_nodes
#     assert reporter.required_nodes == rm.required_nodes
#
#
# def test_reporter_maker_validation():
#     with pytest.raises(TypeError, match="chainable must be an instance of Chainable subclass"):
#         ReporterMaker(object())  # noqa
#
#
# # test reporter
# def test_reporter_creation(nodes):
#     reporter = Reporter(nodes, 2)
#     assert reporter.counter == {node: [] for node in nodes}
#     assert reporter.required_nodes == 2
#     assert reporter._failures == []
#
#
# @pytest.mark.parametrize('combination, rate, succeeded, failed, missed', [
#     param([[True], [True], [True], [True]], 4/4, 4, 0, 0, id="single success marks"),
#     param([[True, True, True, True], [True], [True], [True, True]], 8/8, 8, 0, 0, id="multiple success marks"),
#     param([[False], [False], [False], [False]], 0/4, 0, 4, 0, id="single fail marks"),
#     param([[False, False], [False], [False], [False, False]], 0/6, 0, 6, 0, id="multiple fail marks"),
#     param([[True], [True], [False], [False]], 2/4, 2, 2, 0, id="single hybrid marks"),
#     param([[True, True, False], [True], [True, False], [False]], (2/3+1+1/2+0)/4, 4, 3, 0, id="multiple hybrid marks"),
#     param([[True], [True], [False], []], 2/4, 2, 1, 1, id="single last one missed"),
#     param([[True, True], [True, False], [], []], (1+1/2+0+0)/4, 3, 1, 2, id="multiple last two missed"),
# ])
# def test_reporter_report(reporter, nodes, combination: list[list[bool]], rate: float, succeeded, failed, missed):
#     for node, states in zip(nodes, combination):
#         for state in states:
#             reporter.mark(node, state)
#     report = reporter.report()
#     assert report == {
#         'rate': rate,
#         'succeeded': succeeded,
#         'failed': failed,
#         'missed': missed,
#         'required': 4,
#         'total': 4,
#         'failures': []
#     }
#
#
# def test_report_failure(nodes):
#     reporter = Reporter(frozenset(nodes), 1)
#     node = nodes[0]
#     error = ValueError('test')
#     reporter.report_failure(node, None, error)
#     assert reporter._failures == [dict(source=node.title, input=None, error=error, fatal=True),]
#
#
# @pytest.mark.parametrize('reps', (0, 1, 2, 3), ids=repr)
# @pytest.mark.parametrize('input, error, fatal', itertools.product((None, ''),
#                                                                   (ValueError('test'), TypeError('test')),
#                                                                   (True, False)), ids=repr)
# def test_report_multiple_failures(reporter, input, error: Exception, fatal: bool, reps: int):
#     node = Node(lambda _: None, name='node_title')
#     node.optional = not fatal
#     for _ in range(reps):
#         reporter.report_failure(node, input, error)
#     assert reporter._failures == [dict(source=node.title, input=input, error=error, fatal=fatal)] * reps
#
#
# @pytest.mark.parametrize('success_stat', (True, False))
# def test_marking_unregistered_node(reporter, success_stat):
#     node = Node(func)
#     with pytest.warns(UserWarning, match=f'unregistered node {node!r} ignored'):
#         reporter.mark(node, success_stat)
