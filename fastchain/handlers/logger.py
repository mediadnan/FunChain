"""
This module contains default logging handlers of chains
"""
from logging import getLogger, Logger, ERROR, INFO
from fastchain.monitoring import FailureDetails, ReportStatistics


fastchain_logger = getLogger('fastchain')


def handle_failure(failure: FailureDetails, logger: Logger = fastchain_logger) -> None:
    source, input, error = failure['source'], failure['input'], failure['error']
    message = f"{source} failed with: {error!r} after receiving {type(input)!r} with the value {input!r}"
    level = ERROR if failure['fatal'] else INFO
    logger.log(level, message, exc_info=error)


def handle_stats(stats: ReportStatistics, logger: Logger = fastchain_logger) -> None:
    ...
