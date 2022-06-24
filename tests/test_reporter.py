import unittest
from fastchain.reporter import Reporter


class TestReporter(unittest.TestCase):

    def setUp(self) -> None:
        self.reporter = Reporter('test', 5)

    def check_report(
            self,
            completed_components: int,
            completed_operations: int,
            failed_components: int,
            failed_operations: int,
            *,
            rate: float = None,
    ):
        report = self.reporter.report()
        self.assertEqual(
            5,
            report.total,
            f"expected total = 5 got {report.total}"
        )
        self.assertEqual(
            completed_components,
            report.completed_components,
            f"expected {completed_components = } got {report.completed_components}"
        )
        self.assertEqual(
            completed_operations,
            report.completed_operations,
            f"expected {completed_operations = } got {report.completed_operations}"
        )
        self.assertEqual(
            failed_components,
            report.failed_components,
            f"expected {failed_components = } got {report.failed_components}"
        )
        self.assertEqual(
            failed_operations,
            report.failed_operations,
            f"expected {failed_operations = } got {report.failed_operations}"
        )
        if rate is not None:
            self.assertAlmostEqual(
                rate,
                report.rate,
                4,
                f"expected {rate = } got {report.rate}"
            )

    def test_reporter_init_without_expected_total(self):
        reporter = Reporter('test')
        self.assertEqual(getattr(reporter, '_title', None), "test")
        self.assertEqual(getattr(reporter, '_total_expected', None), None)
        self.assertEqual(getattr(reporter, '_completed', None), {})
        self.assertEqual(getattr(reporter, '_failures', None), {})

    def test_reporter_init_with_expected_total(self):
        self.assertEqual(getattr(self.reporter, '_title', None), "test")
        self.assertEqual(getattr(self.reporter, '_total_expected', None), 5)
        self.assertEqual(getattr(self.reporter, '_completed', None), {})
        self.assertEqual(getattr(self.reporter, '_failures', None), {})

    def test_5_single_successful_components(self):
        for _ in range(5):
            self.reporter.success(object())
        self.check_report(5, 5, 0, 0, rate=1.0)

    def test_5_multiple_successful_components(self):
        for _ in range(5):
            component = object()
            self.reporter.success(component)
            self.reporter.success(component)
        self.check_report(5, 10, 0, 0, rate=1.0)

    def test_5_single_failing_components(self):
        for _ in range(5):
            self.reporter.failure(object(), {})
        self.check_report(0, 0, 5, 5, rate=0.0)

    def test_5_multiple_failing_components(self):
        for _ in range(5):
            component = object()
            self.reporter.failure(component, {})
            self.reporter.failure(component, {})
        self.check_report(0, 0, 5, 10, rate=0.0)

    def test_hybrid_3s_2f_single(self):
        for _ in range(3):
            self.reporter.success(object())
        for _ in range(2):
            self.reporter.failure(object(), {})
        self.check_report(3, 3, 2, 2, rate=0.6)

    def test_hybrid_3s_2f_multiple(self):
        for _ in range(3):
            component = object()
            self.reporter.success(component)
            self.reporter.success(component)
        for _ in range(2):
            component = object()
            self.reporter.failure(component, {})
            self.reporter.failure(component, {})
            self.reporter.failure(component, {})
        self.check_report(3, 6, 2, 6, rate=0.6)


if __name__ == '__main__':
    unittest.main()
