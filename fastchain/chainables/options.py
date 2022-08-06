from abc import ABC, abstractmethod
from typing import Any

from .base import Chainable, FEEDBACK
from ..monitoring import Reporter


class Option(Chainable, ABC):
    __slots__ = 'member',

    def __init__(self, member: Chainable) -> None:
        super(Option, self).__init__(member.title, member.optional)
        self.member: Chainable = member
        self.__name__ = f"{member.__name__}{self.symbol}"

    @property
    @abstractmethod
    def symbol(self) -> str: pass   # reminder to add this class attribute

    def set_title(self, root: str | None = None, branch: str | None = None):
        self.member.set_title(root, branch)


class Map(Option):
    symbol: str = '*'

    def process(self, inputs: Any, report: Reporter) -> FEEDBACK:
        try:
            iter(inputs)
        except TypeError as error:
            self.member.failure(inputs, error, report)
            return False, None
        return True, self._process(inputs, report)

    def _process(self, args, report):
        for arg in args:
            success, result = self.member.process(arg, report)
            if success:
                yield result
