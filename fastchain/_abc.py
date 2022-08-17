from abc import ABC, abstractmethod
from typing import Any, TypedDict


class FailureDetails(TypedDict):
    """standard failure details dictionary"""
    source: str
    input: Any
    error: Exception
    fatal: bool


class ReportStatistics(TypedDict):
    """standard reporter statistics dictionary"""
    rate: float
    successes: int
    failures: int
    total: int
    required: int
    missed: int


class ReporterBase(ABC):
    @abstractmethod
    def __call__(self, component, success: bool) -> None: ...
    @abstractmethod
    def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None: ...
    @abstractmethod
    def statistics(self) -> ReportStatistics: ...
    @abstractmethod
    def _failures(self) -> tuple[FailureDetails]: ...


class ChainableBase(ABC):
    NAME: str
    name: str
    title: str
    optional: bool
    @abstractmethod
    def __len__(self) -> int: ...
    @abstractmethod
    def default_factory(self) -> Any: ...
    @abstractmethod
    def process(self, input, report: ReporterBase) -> tuple[bool, Any]: ...
    @abstractmethod
    def set_title(self, root: str | None = None, branch: str | None = None) -> None: ...
