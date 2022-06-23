import functools
import unittest
from logging import Logger
from typing import Any, Tuple

from funchain.wrapper import Wrapper
from funchain.elements import ChainGroup, ChainableNode, ChainMapOption, ChainFunc, ChainModel
from funchain.reporter import Reporter, Report


class Chainable(ChainableNode):

    def __init__(self, i: int = None):
        super(Chainable, self).__init__("test-group", f"test{'' if i is None else f'-{i}'}")

    def _context(self, arg: int, reporter: Reporter = None, log: Logger = None) -> Tuple[bool, Any]:
        if reporter:
            reporter.success(self)
        return True, arg + 1

    def __repr__(self):
        return f"Chainable({self.title})"


class TestChainable(unittest.TestCase):

    def setUp(self) -> None:
        self.chainables = tuple(Chainable(i) for i in range(3))
        self.chainable = functools.reduce(Chainable.chain, self.chainables)

    def test_initialization_defaults(self):
        chainable = Chainable()
        self.assertEqual(None, chainable.next)
        self.assertEqual(None, chainable.previous)
        self.assertEqual(None, chainable.root)
        self.assertEqual(f'test-group :: test {(0, )}', str(chainable))
        self.assertEqual('test', chainable.title)

    def test_chained_component(self):
        self.assertEqual('test-2', self.chainable.title)
        self.assertEqual((2,), self.chainable.position)
        self.assertEqual(None, self.chainable.next)

    def test_navigation(self):
        self.assertIs(self.chainables[1], self.chainable.previous)
        self.assertIs(self.chainables[0], self.chainable.previous.previous)
        self.assertIs(self.chainables[0], self.chainable.first)
        self.assertIs(self.chainable, self.chainable.first.last)
        self.assertIs(self.chainables[1], self.chainable.first.next)
        self.assertIs(self.chainables[2], self.chainable.first.next.next)

    def test_size(self):
        self.assertEqual(3, len(self.chainable.first))
        self.assertEqual(2, len(self.chainable.first.next))
        self.assertEqual(1, len(self.chainable.first.next.next))

    def test_navigation_groups(self):
        self.assertIsInstance(self.chainable.sequence, tuple)
        self.assertEqual(3, len(self.chainable.sequence))
        self.assertEqual(tuple(self.chainables), self.chainable.sequence)
        self.assertEqual((), self.chainable.roots)
        self.assertEqual(tuple(self.chainables[:2]), self.chainable.previous_all)
        self.assertEqual((), self.chainable.next_all)
        self.assertEqual(tuple(self.chainables[1:]), self.chainable.first.next_all)
        self.assertEqual((), self.chainable.first.previous_all)


class TestChainMapOption(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = ChainMapOption('test-group')
        self.mapper.chain(Chainable())

    def check_reports(
            self,
            report: Report,
            completed_components: int,
            completed_operations: int,
            failed_components: int,
            failed_operations: int,
    ):
        self.assertEqual(completed_components, report.completed_components, "unexpected completed_components value")
        self.assertEqual(completed_operations, report.completed_operations, "unexpected completed_operations value")
        self.assertEqual(failed_components, report.failed_components, "unexpected failed_components value")
        self.assertEqual(failed_operations, report.failed_operations, "unexpected failed_operations value")

    def test_mapping(self):
        self.assertEqual((True, (2, 3, 4, 5)), self.mapper((1, 2, 3, 4)))

    def test_reporting(self):
        reporter = Reporter('test', 2)
        self.check_reports(reporter.report(), 0, 0, 0, 0)
        self.assertEqual((True, (2, 3, 4)), self.mapper((1, 2, 3), reporter))
        self.check_reports(reporter.report(), 2, 4, 0, 0)


class TestChainFunc(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.add_one = ChainFunc(Wrapper(lambda x: x + 1, title='add_one'), 'test-group')

    def test_successful_operation(self):
        self.assertEqual((True, 5), self.add_one(4))
        self.assertEqual((True, 0), self.add_one(-1))
        self.assertEqual((True, 4.6), self.add_one(3.6))

    def test_successful_operation_report(self):
        reporter = Reporter('test', 1)
        self.assertEqual(0, reporter.report().completed_components)
        self.assertEqual(0, reporter.report().completed_operations)
        self.assertEqual(0, reporter.report().failed_components)
        self.assertEqual(0, reporter.report().failed_operations)
        self.assertEqual((True, 5), self.add_one(4, reporter))
        self.assertEqual(1, reporter.report().completed_components)
        self.assertEqual(1, reporter.report().completed_operations)
        self.assertEqual(0, reporter.report().failed_components)
        self.assertEqual(0, reporter.report().failed_operations)

    def test_failed_operation(self):
        self.assertEqual((False, None), self.add_one("string"))
        self.assertEqual((False, None), self.add_one(None))
        self.assertEqual((False, None), self.add_one(()))

    def test_failed_operation_report(self):
        reporter = Reporter('test', 1)
        self.assertEqual(0, reporter.report().completed_components)
        self.assertEqual(0, reporter.report().completed_operations)
        self.assertEqual(0, reporter.report().failed_components)
        self.assertEqual(0, reporter.report().failed_operations)
        self.assertEqual((False, None), self.add_one(None, reporter))
        self.assertEqual(0, reporter.report().completed_components)
        self.assertEqual(0, reporter.report().completed_operations)
        self.assertEqual(1, reporter.report().failed_components)
        self.assertEqual(1, reporter.report().failed_operations)


class TestChainGroup(unittest.TestCase):

    def setUp(self) -> None:
        self.chainables = tuple(Chainable(i) for i in range(3))
        self.group = ChainGroup(self.chainables, 'test_group')

    def test_initialization(self):
        self.assertEqual(self.group.members, set(self.chainables))
        for chainable in self.chainables:
            self.assertIs(chainable.root, self.group)

    def test_chaining_members(self):
        chainables = Chainable(), Chainable()
        self.assertIs(chainables[0].next, None)
        self.assertIs(chainables[1].next, None)
        self.assertIs(chainables[0].previous, None)
        self.assertIs(chainables[1].previous, None)

        ChainGroup(chainables, 'test_group')
        self.assertIs(chainables[0].next, chainables[1])
        self.assertIs(chainables[1].next, None)
        self.assertIs(chainables[0].previous, None)
        self.assertIs(chainables[1].previous, chainables[0])

    def test_check_entry(self):
        self.assertIs(self.group.entry, self.chainables[0])

    def test_isolation(self):
        chain = self.group.chain(Chainable())
        self.assertIs(chain, self.group.next)
        self.assertEqual(4, len(self.group))
        self.assertEqual(3, self.group.size)
        self.assertEqual((True, 5), self.group.entry(2))
        self.assertEqual((True, 6), self.group(2))

    def test_subscription(self):
        for i in range(3):
            self.assertIs(self.group[i], self.chainables[i])


class TestChainModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.group = ChainGroup(tuple(Chainable(i) for i in range(3)), 'test-group')
        cls.chainable = Chainable()

    def setUp(self) -> None:
        self.model = ChainModel({
            'member-1': self.group,
            'member-2': self.chainable
        }, 'test-group')

    def test_initialization(self):
        self.assertIs(self.group.root, self.model)
        self.assertIs(self.chainable.root, self.model)
        self.assertEqual({self.chainable, self.group}, self.model.members)
        self.assertEqual({
            'member-1': self.group,
            'member-2': self.chainable
        }, self.model.model)

    def test_subscription(self):
        self.assertIs(self.model['member-1'], self.group)
        self.assertIs(self.model['member-2'], self.chainable)

    def test_size(self):
        self.model.chain(Chainable())
        self.assertEqual(4, self.model.size)
        self.assertEqual(5, len(self.model))


if __name__ == '__main__':
    unittest.main()
