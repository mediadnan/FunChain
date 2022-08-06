import pytest
import logging
from fastchain.monitoring import Reporter, LoggingHandler, RaiseFailureHandler


class TestReporter:

    @staticmethod
    def get_handlers_combination():
        return [
            pytest.param([], id="no_handler"),
            pytest.param([LoggingHandler('test')], id="logging_hand_only"),
            pytest.param([RaiseFailureHandler('test')], id="raise_hand_only"),
            pytest.param([LoggingHandler('test'), RaiseFailureHandler('test')], id="all_handlers"),
        ]

    @staticmethod
    def get_required_combinations():
        return [0, 1, 2, 3, 4]

    @pytest.fixture
    def components(self):
        return {object() for _ in range(4)}

    @pytest.fixture
    def reporter(self, components, required):
        return Reporter(components, required, [])

    @pytest.mark.parametrize('handlers', get_handlers_combination())
    @pytest.mark.parametrize('required', get_required_combinations())
    def test_report_creation(self, components, required, handlers):
        reporter = Reporter(components, required, handlers)  # type: ignore
        assert isinstance(reporter, Reporter)
        assert isinstance(reporter.counter, dict) and all(isinstance(v, list) for v in reporter.counter.values())
        assert isinstance(reporter.failures, list)
        assert reporter.required == required
        assert reporter.failure_handlers == handlers


@pytest.fixture
def failure():
    return {
        'source': 'test',
        'input': None,
        'error': Exception('test exception'),
        'fatal': True,
    }


def test_logging_handler(caplog, failure):
    lh = LoggingHandler('tests')
    assert isinstance(lh.logger, logging.Logger)
    with caplog.at_level(logging.ERROR):
        lh(failure)
        assert caplog.text
    # pattern = re.compile(r"^ERROR tests::test raised Exception\('test exception'\) after receiving None \(type: NoneType\) at \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")  # noqa
    # assert pattern.match(caplog.records[-1].msg)
