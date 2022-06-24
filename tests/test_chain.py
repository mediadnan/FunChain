import unittest
import warnings
from typing import Iterable, Type

from funchain.chain import parse, Chain, SUPPORTED_CHAINABLE_OBJECTS
from funchain.elements import ChainGroup, ChainFunc, ChainableNode, ChainModel, ChainMapOption
from funchain.wrapper import Wrapper, chainable, funfact
from funchain.reporter import Report


class TestParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.func = Wrapper(lambda x: 2 * x + 1, title='arithmetics')

    @staticmethod
    def parse(*chainables):
        return parse('test', chainables)

    def check_output(
            self,
            obj,
            tp: Type[ChainableNode],
            ln: int = ...,
    ):
        self.assertIsInstance(obj, tp)
        if ln is not ...:
            self.assertEqual(ln, len(obj))

    def test_parsing_allowed_values(self):
        self.assertIsInstance(self.parse(str), ChainFunc)
        self.assertIsInstance(self.parse((str, )), ChainFunc)
        self.assertIsInstance(self.parse(str.strip, str.upper), ChainGroup)
        self.assertIsInstance(self.parse({'upper': str.strip, 'lower': str.lower}), ChainModel)
        self.assertIsInstance(self.parse('*'), ChainMapOption)

    def test_parsing_forbidden_values(self):
        self.assertRaises(ValueError, self.parse)
        self.assertRaises(ValueError, self.parse, None)
        self.assertRaises(ValueError, self.parse, 'bla-bla')
        self.assertRaises(ValueError, self.parse, ())
        self.assertRaises(ValueError, self.parse, {})

    def test_chaining_grouping(self):
        group = self.parse(self.func, self.func, self.func)
        self.check_output(group, ChainGroup, 3)
        self.assertEqual(None, group.root)
        self.assertEqual(3, len(group.members))
        self.assertIs(next(iter(group.members)).root, group)
        self.assertEqual(3, len(group.entry))

        self.assertEqual(2, len(group.entry.next))

        self.assertEqual(1, len(group.entry.next.next))


class TestChain(unittest.TestCase):

    def setUp(self) -> None:
        self.report = None

    def set_report(self, report: Report) -> None:
        self.report = report

    def chain(self, *chainables: SUPPORTED_CHAINABLE_OBJECTS, number: int = None) -> Chain:
        from random import randint
        if number is None:
            number = randint(10, 99)
        return Chain(*chainables, title=f"test_chain{number}", callback=self.set_report)

    def check_report(
            self,
            completed: int,
            failed: int,
            *,
            in_failures: Iterable[str] = None,
    ):
        self.assertIsNot(self.report, None)
        self.assertEqual(completed, self.report.completed_components)
        self.assertEqual(failed, self.report.failed_components)
        if in_failures is not None:
            for identity in in_failures:
                self.assertIn(identity, self.report.failures)

    def test_chain_with_empty_structure(self):
        self.assertRaises(ValueError, Chain, title="test")

    def test_title_duplication_warning(self):
        with warnings.catch_warnings(record=True) as cm:
            chain = Chain(int, title='test')
            self.assertEqual(0, len(cm))
        with self.assertWarns(UserWarning):
            Chain(str, title='test')
        del chain
        with warnings.catch_warnings(record=True) as cm:
            Chain(int, title='test')
            self.assertEqual(0, len(cm))

    def test_chain_creation(self):
        title = 'abs_str_num'
        chain = Chain(int, abs, title=title)
        self.assertEqual(2, len(chain))
        self.assertEqual(title, chain.title)
        self.assertEqual(5, chain("-5"))
        self.assertIsInstance(chain.core, ChainableNode)

    def test_reporter_successful(self):
        from math import sqrt
        chain = self.chain(float, sqrt, round)
        self.assertEqual(4, chain("   17  "))
        self.check_report(3, 0)

    def test_reporter_unsuccessful_1(self):
        from math import sqrt
        chain = self.chain(float, sqrt, round, number=0)
        self.assertEqual(None, chain("a34"))
        self.check_report(0, 1, in_failures=(f'test_chain0 :: float {(0, 0)}', ))

    def test_reporter_unsuccessful_2(self):
        from math import sqrt
        chain = self.chain(float, sqrt, round, number=1)
        self.assertEqual(None, chain("-5"))
        self.check_report(1, 1, in_failures=(f'test_chain1 :: sqrt {(0, 1)}', ))


if __name__ == '__main__':
    unittest.main()
