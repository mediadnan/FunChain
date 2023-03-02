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
from types import TracebackType
from typing import Any, overload, Self, Callable

from ._util import pascal_to_snake




class Severity(IntEnum):
    """Defines levels of severity, each with different failure reaction"""
    def __new__(cls, value, doc=None):
        # Adding docstring to Enum members, idea form:
        # https://stackoverflow.com/questions/50473951/how-can-i-attach-documentation-to-members-of-a-python-enum
        self = object.__new__(cls)  # calling super().__new__(value) here would fail
        self._value_ = value
        if doc is not None:
            self.__doc__ = doc
        return self

    OPTIONAL = -1, "Basically indicates that the failure should be ignored"
    NORMAL = 0, "Indicates that the failure should be reported but without failure"
    INHERIT = 0, "The same as NORMAL, but could be overriden by any other severity"
    REQUIRED = 1, "Indicates that the failure should be handled and the process should stop"


# severity shortcuts
OPTIONAL = Severity.OPTIONAL
NORMAL = Severity.NORMAL
INHERIT = Severity.INHERIT
REQUIRED = Severity.REQUIRED


class Failure(Exception):
    """
    Custom exception holding description and additional details,
    this exception can be raised inside nodes if a some
    condition is not met, as a form of validation.
    """
    description: str
    details: dict[str, Any]

    def __init__(self, description: str, **details):
        super().__init__(description)
        self.description = description
        self.details = details


@dataclass(slots=True, kw_only=True, order=False, frozen=True)
class FailureData:
    """
    Structured failure data automatically created by fastchain.reporter.Reporter,
    this object holds key information about a specific processing failure.

    :param source: dot-separated location where the failure occurred (path.to.source)
    :type source: str
    :param description: describes what's gone wrong that cause a failure
    :type description: str
    :param datetime: tells when the failure occurred
    :type datetime: datetime
    :param severity: tells how serious the failure was (defines how to react to the failure)
    :type severity: Severity
    :param details: additional key-value pairs information about the failure (depends on the source)
    :type details: dict[str, Any]
    """
    source: str
    description: str
    datetime: datetime
    severity: Severity = field(default=Severity.INHERIT)
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
                            'r' will override old logs each time called.
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


    def __call__(self, failure: FailureData):
        lvl = logging.ERROR if (failure.severity is REQUIRED) else logging.WARNING
        self._logger.log(lvl, failure.description, extra={'failure_source': failure.source,})


class Reporter:
    _name: str | None
    _root: Self | None
    _severity: Severity
    _details: dict[str, Any]
    _handler: Callable[[FailureData], None] | None

    def __init__(
            self,
            name: Any = None,
            severity: Severity = INHERIT,
            handler: Callable[[FailureData], None] | None = FailureLogger(),
            **details
    ) -> None:
        """
        Reporter holds tracing info when called by nested nodes, to keep track
        of the location (source) of error and holds additional information
        from each layer to combine when a failure occurs.

        The severity of the reporter determines how it reacts to a specific failure.

        :param name: name of the new reporter
        :param severity: level of severity OPTIONAL/NORMAL/REQUIRED
        :param handler: function that will be called with FailureDetails object
        :keyword details: additional details to be reported
        """
        self._root = None
        self._name = name
        self._handler = handler
        self._details = details
        self._severity = severity

    def __call__(self, name: Any, severity: Severity = INHERIT, **details) -> Self:
        """
        Derives new reporter from the current, keeping its reference.

        :param name: name of the new sub reporter
        :param severity: level of severity OPTIONAL/NORMAL/REQUIRED
        :keyword details: additional details to be reported
        :return: the new reporter child
        """
        sub = self.__class__(name, severity, self._handler, **details)
        sub._root = self
        return sub

    def __enter__(self) -> Self:
        """Reporter as a context will capture exceptions and report them"""
        return self

    def __exit__(
            self,
            exc_type: type[Exception] | None,
            exc_val: Exception | None,
            exc_tb: TracebackType
    ) -> bool:
        if exc_type is None:
            return True
        elif isinstance(exc_val, Exception):
            self.report(exc_val)
            return True
        return False  # propagate higher order exception (like BaseException)

    @property
    def name(self) -> str | None:
        """Gets dot separated hierarchical name root.sub.sub_sub"""
        if (root := self._root) and (root_name := root.name):
            return f'{root_name}.{self._name}'
        return self._name

    @property
    def details(self) -> dict[str, Any]:
        """Gets full (hierarchically merged) details"""
        if (root := self._root) and (root_context := root.name):
            return {**root_context, **self._details}
        return self._details.copy()

    @property
    def severity(self) -> Severity:
        """Gets the (root aware) severity"""
        return self._root.severity if (severity := self._severity is INHERIT) else severity

    @overload
    def report(self, error: Exception, severity: Severity = ..., **details) -> None: ...
    @overload
    def report(self, description: str, severity: Severity = ..., **details) -> None: ...

    def report(self, arg: str | Exception, **details) -> None:
        """Encapsulate the failure with registered details into a FailureDetails object and calls the handler"""
        severity = self.severity
        handler = self._handler
        if (severity is OPTIONAL) or (handler is None):
            return
        dt = datetime.now()
        if isinstance(arg, Failure):
            desc = arg.description
            details = {**self.details, **details, **arg.details}
        elif isinstance(arg, Exception):
            desc = str(arg)
            details = {**self.details, **details, 'error_type': pascal_to_snake(type(arg).__name__)}
        else:
            desc = arg
            details = {**self.details, **details}
        handler(FailureData(
            source=self.name,
            description=desc,
            datetime=dt,
            severity=severity,
            details=details
        ))
