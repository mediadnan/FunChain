import re

import pytest
from logging import getLogger, INFO, ERROR

from fastchain._abc import FailureDetails
from fastchain.monitoring import LoggingHandler


@pytest.mark.parametrize('print_stats', (True, False))
def test_logging_handler_bad_args_creation(print_stats):
    with pytest.raises(TypeError):
        LoggingHandler(object(), print_stats)  # noqa


@pytest.mark.parametrize('print_stats', (True, False))
@pytest.mark.parametrize('input, logger', ((None, getLogger('fastchain')), (getLogger('test'), getLogger('test'))))
def test_logging_handler_creation(input, logger, print_stats):
    lh = LoggingHandler(input, print_stats)
    assert lh.logger is logger
    assert lh.print_stats is print_stats


@pytest.mark.parametrize('failure, level', [
    (FailureDetails(source='test', input=None, error=Exception('test failure'), fatal=True), ERROR),
    (FailureDetails(source='test', input=None, error=Exception('test failure'), fatal=False), INFO),
])
def test_failures_handling(caplog, failure, level):
    logger = getLogger('test_logger')
    lh = LoggingHandler(logger, False)
    with caplog.at_level(level, logger.name):
        lh.handle_report(dict(rate=1, succeeded=3, failed=1, missed=0, required=2, total=3, failures=[failure]))
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == level
    assert caplog.records[0].message == "test raised Exception('test failure') when receiving <class 'NoneType'>: None"


def test_stats_handling(capfd):
    logger = getLogger('test_logger')
    lh1 = LoggingHandler(logger, True)
    report = dict(rate=1, succeeded=2, failed=0, missed=0, required=1, total=2, failures=[])
    lh1.handle_report(report)
    cap = capfd.readouterr()
    assert re.search(
        r'success percentage:\s*100%\s*'
        r'successful operations:\s*2\s*'
        r'unsuccessful operations:\s*0\s*'
        r'unreached nodes:\s*0\s*'
        r'required nodes:\s*1\s*'
        r'total number of nodes:\s*2',
        cap.out,
        re.MULTILINE
    )
