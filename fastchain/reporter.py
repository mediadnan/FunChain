"""
fastchain.reporter module contains the Reporter object definition,
used to keep trace and state between nested node calls and keeps
references to (default or custom) failure handler.

The module also defines a fastchain universal enumerator for different
levels of failure reaction called Severity; and defines 3 levels
OPTIONAL for expected failures, NORMAL for less important failures
and REQUIRED for tolerated failures, a user defined handler
should raise some kind of exception when a failure with that severity level
is received (such as an expressive HTTPException for http/rest APIs)

This module contains a default (simple) failure handler, that simply
logs failures to the stdout (console/terminal) to get you started,
in production environment, you might want to push failures
to a pub/sub service and handle them more seriously.
"""
import logging
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime
from os import PathLike
from typing import Any, Callable, Self, TypeAlias

from .util.names import NAME_SEPARATOR


class Severity(IntEnum):
    """
    Defines different levels of severity, each one for a different failure reaction

    OPTIONAL
        Basically indicates that the failure should be ignored

    NORMAL
        Indicates that the failure should be reported but without failure

    REQUIRED
        Indicates that the failure should be handled and the process should stop
    """
    OPTIONAL = 0
    NORMAL = 1
    REQUIRED = 2


# severity shortcuts
OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
REQUIRED = Severity.REQUIRED


@dataclass(order=False, frozen=True, slots=True)
class Failure:
    """
    Structured failure data automatically created by fastchain.reporter.Reporter,
    this object holds key information about a specific processing failure.

    :param source: dot-separated location where the failure occurred (path.to.source)
    :param error: describes what's gone wrong that cause a failure
    :param severity: tells how serious the failure was (defines how to react to the failure)
    :param datetime: tells when the failure occurred
    :param details: additional key-value pairs information about the failure (depends on the source)
    """
    source: str
    error: Exception
    severity: Severity = field(default=NORMAL)
    datetime: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict, repr=False)


class FailureLogger:
    _logger: logging.Logger

    def __init__(
            self,
            _name: str = 'FastChain',
            _format: str = "%(failure_source)s [%(levelname)s] :: %(message)s (%(asctime)s)",
            _file: str | PathLike[str] | None = None,
            _write_mode: str = 'a',
    ) -> None:
        """
        FailureLogger is the default failure handler, which logs failures
        to the standard output without raising exceptions.

        :param _name: The name of the logger
        :type _name: str
        :param _format: log formatting template https://docs.python.org/3/library/logging.html#formatter-objects
        :type _format: str
        :param _file: a fully qualified file name for logs (path/to/logs.txt),
                      default is None (which deactivate writing logs to a file)
        :type _file: str | PathLike[str] | None
        :param _write_mode: the writing mode, default 'a' for append, which adds logs to the file,
                            'w' will override old logs each time called.
        :type _write_mode: str
        """
        formatter = logging.Formatter(_format, defaults={'failure_source': ''})
        logger = logging.getLogger(_name)
        logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        if isinstance(_file, (str, PathLike)):
            file_handler = logging.FileHandler(_file, _write_mode)
            file_handler.setLevel(logging.WARNING)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        self._logger = logger

    def __call__(self, failure: Failure):
        lvl = logging.ERROR if (failure.severity is REQUIRED) else logging.WARNING
        self._logger.log(lvl, failure.error, extra={'failure_source': failure.source, })


FailureHandler: TypeAlias = Callable[[Failure], None]


class Reporter:
    __slots__ = 'name', 'handler', 'severity', 'details'
    name: str
    severity: Severity
    details: dict[str, Any]
    handler: FailureHandler | None

    def __init__(
            self,
            name: str,
            handler: FailureHandler | None,
            *,
            severity: Severity = NORMAL,
            **details
    ) -> None:
        """
        Reporter object holds location information of nodes
        and handles their failures.

        :param name: the root name of the chain execution
        :param handler: the function to be called when failures occur
        :param severity: the level of severity (OPTIONAL, NORMAL, REQUIRED)
        :param details: any additional details to be reported
        """
        self.name = name
        self.details = details
        self.handler = handler
        self.severity = severity

    def failure(self, error: Exception) -> None:
        """Prepares a failure object and calls the handler"""
        if (self.severity is OPTIONAL) or (self.handler is None):
            return
        self.handler(Failure(self.name, error, self.severity, details=self.details))

    def __call__(self, name: str | None = None, *, severity: Severity = NORMAL, **details) -> Self:
        """Derives a new reporter with a hierarchical name from the current one"""
        return Reporter(
            self.name if name is None else f'{self.name}{NAME_SEPARATOR}{name}',
            self.handler,
            severity=severity,
            **{**self.details, **details}
        )

    def __enter__(self) -> Self:
        """Reporter as a context will capture exceptions and report them"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is None:
            return True
        elif isinstance(exc_val, Exception):
            self.failure(exc_val)
            return True
        return False  # propagate higher order exception (like BaseException)
