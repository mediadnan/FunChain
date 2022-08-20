import pytest
from logging import getLogger, INFO
from fastchain.chainables.base import Node
from fastchain.monitoring import LoggingHandler


@pytest.mark.parametrize('print_stats', (True, False))
def test_logging_handler_bad_args_creation(print_stats):
    with pytest.raises(TypeError):
        LoggingHandler(object(), print_stats)


@pytest.mark.parametrize('print_stats', (True, False))
@pytest.mark.parametrize('input, logger', ((None, getLogger('fastchain')), (getLogger('test'), getLogger('test'))))
def test_logging_handler_creation(input, logger, print_stats):
    lh = LoggingHandler(input, print_stats)
    assert lh.logger is logger
    assert lh.print_stats is print_stats


@pytest.mark.skip
def test_report_handling(caplog):
    logger = getLogger('test_logger')
    lh = LoggingHandler(logger, True)
    error = Exception('test error')
    with caplog.at_level(INFO):
        lh.handle_report({'input': None, 'source': Node(lambda x: x), 'error': error})
