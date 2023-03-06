from datetime import datetime

import pytest
import logging

from fastchain.reporter import (
    Severity,
    OPTIONAL,
    NORMAL,
    INHERIT,
    REQUIRED,
    FailureData,
    FailureLogger,
)


def test_severity_values():
    """Severity values MUST be constant through minor and patch versions at least"""
    assert Severity.OPTIONAL is OPTIONAL
    assert Severity.NORMAL is NORMAL
    assert Severity.INHERIT is INHERIT
    assert Severity.REQUIRED is REQUIRED
    assert OPTIONAL.value == -1
    assert NORMAL.value == 0
    assert INHERIT.value == 0
    assert REQUIRED.value == 1


def test_failure_data_object():
    time = datetime.now()
    fd = FailureData(
        'path.to.failure.source',
        'mock failure for test',
        time,
        REQUIRED,
        dict(additional='details')
    )
    assert fd.source == 'path.to.failure.source'
    assert fd.description == "mock failure for test"
    assert fd.datetime == time
    assert fd.severity is REQUIRED
    assert fd.details['additional'] == "details"


@pytest.mark.parametrize('severity, log_level, log_name', [
    (NORMAL, logging.WARNING, 'WARNING'),
    (REQUIRED, logging.ERROR, 'ERROR'),
])
def test_failure_logger(caplog, severity, log_level, log_name):
    logger_name = 'FastChain'
    logger = FailureLogger(logger_name)
    dt = datetime(2023, 6, 6)
    assert logger._logger.name == logger_name, "Logger name should be set by FailureLogger constructor"
    with caplog.at_level(log_level, logger_name):
        logger(FailureData('path.to.source', 'test message', dt, severity=severity))
    log_record = caplog.records.pop()
    assert log_record.levelno == log_level, "Logging level should reflect the severity level"
    assert (log_record.message == f"path.to.source [{log_name}] :: test message 2023-06-06 00:00:00",
            "The log template should match the default format")


def test_failure_file_logging(tmp_path):
    log_file = tmp_path/'logs.txt'
    dt = datetime(2023, 6, 6)
    assert not log_file.exists(), "File should not exist"
    logger = FailureLogger(_file=log_file)
    failure = FailureData('failure.source', 'failed for test', dt)
    logger(failure)
    assert (log_file.read_text() == f"path.to.source [WARNING] :: test message 2023-06-06 00:00:00",
            "File log should match the default format")
