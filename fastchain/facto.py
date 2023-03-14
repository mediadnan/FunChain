import functools
from typing import overload, Callable, Any, Self

from fastchain.reporter import Severity
from fastchain._util import get_name, validate_name, is_async, get_varname
# from fastchain.node import *


class node:
    """
    node() is a utility provided by fastchain to customize the look or behaviour
    of a specific component of the chain.
    """
    __slots__ = ('origin', 'name', 'severity')
    @overload
    def __init__(self, function: Callable[[Any], Any], /, name: str | None = ...) -> None: ...
    @overload
    def __init__(self, function: Callable[[Any], Any], /, name: str | None = ..., *args, **kwargs) -> None: ...
    @overload
    def __init__(self, sequence: tuple, /) -> None: ...
    @overload
    def __init__(self, model: dict | list, /) -> None: ...

    def __init__(
            self,
            origin, /,
            *args,
            _name: str | None = None,
            **kwargs
    ) -> None:
        if callable(origin):
            if _name is None:
                _name = get_name(origin)
            if args or kwargs:
                origin = functools.partial(origin, *args, **kwargs)
        elif isinstance(origin, node):
            raise TypeError("Cannot wrap an already wrapped node")
        self.origin = origin
        self.name = _name
        self.severity = Severity.NORMAL

    def __set_severity(self, severity: Severity) -> None:
        if self.severity is not Severity.NORMAL:
            raise ValueError(f"node severity has already been set to {self.severity.name!r}")
        self.severity = severity

    def optional(self) -> Self:
        self.__set_severity(Severity.OPTIONAL)
        return self

    def required(self) -> Self:
        self.__set_severity(Severity.REQUIRED)
        return self

    def named(self, name: str) -> Self:
        self.name = validate_name(name)
        return self


def build(obj, name: str | None = None):
    pass


if __name__ == '__main__':
    nd = node(lambda x: x*2).named('double').required()
    print('node name is', nd.name)
    print('node severity is', nd.severity.name)
    print('node origin is', nd.origin)
