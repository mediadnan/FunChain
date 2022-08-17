"""
This module contains default logging handlers of chains
"""
from typing import Iterable
from logging import getLogger, Logger, ERROR, INFO
from fastchain.monitoring import FailureDetails, ReportStatistics


fastchain_logger = getLogger('fastchain')


def handle_failure(failures: Iterable[FailureDetails], logger: Logger = fastchain_logger) -> None:
    for failure in failures:
        source, input, error = failure['source'], failure['input'], failure['error']
        message = f"{source} failed with: {error!r} after receiving {type(input)!r} with the value {input!r}"
        level = ERROR if failure['fatal'] else INFO
        logger.log(level, message, exc_info=error)


def handle_stats(stats: ReportStatistics, logger: Logger = fastchain_logger) -> None:
    rate, total, missed, successes, failures, required = (
        stats['rate'], 
        stats['total'],
        stats['missed'],
        stats['successes'],
        stats['failures'],
        stats['required']
    )
    success_msg = 'all nodes have' if rate == 1 else ('no node has' if rate == 0 else f'only {round(rate*100)}% of nodes have')
    operations_succeeded = 'one operation has' if successes == 1 else f'{successes} operations have'
    missed_nodes = 'none is' if missed == 0 else ('one is' if missed == 1 else f'{missed} are')
    required_nodes = '1 is' if required == 1 else f'{required} are'
    total_nodes = 'one node' if total == 1 else f'{total} nodes'
    
    message = f"{success_msg} succeeded. summary: {operations_succeeded} succeeded and {failures} failed, " \
              f"{total_nodes} in total from which {required_nodes} required"
