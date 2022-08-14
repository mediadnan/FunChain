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
    success_rate: float
    minimum_expected_rate: float
    successful_node_operations: int
    failed_node_operations: int
    missed_nodes: int
    total_nodes: int


class ReporterBase(ABC):
    failures: list[FailureDetails]
    @abstractmethod
    def __call__(self, component, success: bool) -> None: ...
    @abstractmethod
    def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None: ...
    @abstractmethod
    def statistics(self) -> ReportStatistics: ...


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
