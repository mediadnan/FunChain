from abc import ABC, abstractmethod
from typing import Any, TypedDict


class FailureDetails(TypedDict):
    """standard fd details dictionary"""
    source: str
    input: Any
    error: Exception
    fatal: bool


class ReportDetails(TypedDict):
    """standard reporter statistics dictionary"""
    rate: float
    succeeded: int
    failed: int
    missed: int
    required: int
    total: int
    failures: list[FailureDetails]


class ReporterBase(ABC):
    @abstractmethod
    def mark(self, node: 'ChainableBase', success: bool) -> None: ...
    @abstractmethod
    def report_failure(self, source: 'ChainableBase', input, error: Exception) -> None: ...
    @abstractmethod
    def report(self) -> ReportDetails: ...


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
