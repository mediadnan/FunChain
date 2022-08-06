from abc import ABC, abstractmethod
from typing import Any


class ReporterBase(ABC):
    @abstractmethod
    def __call__(self, component, success: bool) -> None: ...
    @abstractmethod
    def register_failure(self, source: str, input, error: Exception, fatal: bool = False) -> None: ...
    @abstractmethod
    def report(self) -> dict[str, Any]: ...


class ChainableBase(ABC):
    @abstractmethod
    def process(self, input, report: ReporterBase) -> tuple[bool, Any]: ...
    @abstractmethod
    def set_title(self, root: str | None = None, branch: str | None = None) -> None: ...
