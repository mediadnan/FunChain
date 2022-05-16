import inspect
from typing import Callable, Any, Tuple, Dict, Union

CHAINABLE_FUNC_TYPE = Callable[[Any], Any]
DICT_MODEL_TYPE = Dict[Any, Union['Chainable', Tuple['Chainable']]]
FAILURE_REPORTER_TYPE = Callable[[str, Exception], None]


class ChainError(Exception):
    """exception that get triggered when a chained function fails"""


class Chainable:
    __slots__ = '__name', '__multiple', '__async', '__default', '__function'

    __name: str
    __multiple: bool
    __async: bool
    __default: bool
    __function: CHAINABLE_FUNC_TYPE

    def __init__(
            self,
            name: str,
            function: CHAINABLE_FUNC_TYPE,
            *,
            multiple: bool = False,
            default: Any = None
    ) -> None:
        self.__name = name
        self.__multiple = multiple
        self.__async = inspect.iscoroutinefunction(function)
        self.__default = default
        self.__function = function

    @property
    def name(self) -> str:
        return self.__name

    @property
    def multiple(self):
        return self.__multiple

    @property
    def coroutine(self) -> bool:
        return self.__async

    @property
    def default(self) -> Any:
        return self.__default

    def __call__(self, arg: Any) -> Any:
        return self.__function(arg)


class Chain:

    __name: str
    __chain: Tuple[Chainable]
    __len: int
    __failure_report: FAILURE_REPORTER_TYPE
    __debug: bool

    def __init__(
            self,
            title: str,
            *chainables: Chainable | DICT_MODEL_TYPE,
            namespace: str = None,
            failure_report: FAILURE_REPORTER_TYPE = None,
            debug: bool = False,
            **kwargs
    ) -> None:
        self.__len = 0
        self.__debug = debug
        self.__make_identity(title, namespace=namespace, parent_title=kwargs.get('parent_title'))
        self.__failure_report = failure_report or default_failure_callback
        self.__chain = tuple(map(self._bundle, chainables))

    def __make_identity(self, title: str, *, namespace: str = None, parent_title: str = None) -> None:
        """creates a chain name"""

        if not isinstance(title, str):
            raise TypeError("title must be a string")
        elif not title:
            raise ValueError("title should not be empty")

        if parent_title:
            if not isinstance(parent_title, str):
                raise TypeError("parent_title must be a string")
            self.__name = f"{parent_title} / {title}"

        elif namespace:
            if not isinstance(namespace, str):
                raise TypeError("namespace must be a string")
            self.__name = f"[{namespace}] :: {title}"

        else:
            self.__name = title

    @property
    def name(self) -> str:
        """read-only property that returns the chain name"""
        return self.__name

    def _chainable_name(self, chainable: str) -> str:
        """appends the chainable component's name to the chain name"""
        return f"{self.__name} [{chainable}]"

    def _bundle(self, obj: Union[Chainable, DICT_MODEL_TYPE]) -> Chainable:
        """converts a compatible data structure to a chainable object"""
        if isinstance(obj, Chainable):
            return obj

        elif isinstance(obj, dict):
            new_obj = dict()
            for key, value in obj.items():
                if not isinstance(value, (tuple, list)):
                    value = (value, )
                new_obj[key] = Chain(
                    key,
                    *value,
                    failure_report=self.__failure_report,
                    parent_title=self.__name
                )
            return dict_to_chainable(new_obj)

        elif isinstance(obj, (tuple, list)):
            ...

        else:
            raise TypeError(f"'{type(obj)}' is not supported by the chain handler")

    def _call_context(self, param: Any, chainable: Chainable) -> Tuple[bool, Any]:
        """calls the chainable object in a save context and returns the result and a success flag"""
        try:
            return True, chainable(param)
        except Exception as error:
            self.__failure_report(self._chainable_name(chainable.name), error)
            return False, chainable.default

    def _record(self, health: bool, chainable: Chainable) -> None: ...

    def _sequence(self, param: Any, *chainables: Chainable) -> Any:
        """recursive function that pipes results from previous chainable function to the next"""

        chainable, *chainables = chainables
        flag, result = self._call_context(param, chainable)
        self._record(flag, chainable)

        if not (flag and chainables):
            return result

        elif not chainable.multiple:
            return self._call_context(result, *chainables)
        else:
            try:
                mapper = map(lambda p: self._sequence(p, *chainables), result)
            except TypeError as error:
                self.__failure_report(self._chainable_name(f'{chainable.name}-mapper'), error)
                return chainable.default
            return tuple(mapper)

    def __call__(self, param: Any) -> Any:
        return self._sequence(param, *self.__chain)


def make_identity(title: str, *, namespace: str = None, parent_title: str = None) -> str:
    """creates a chain name"""
    if not isinstance(title, str):
        raise TypeError("title must be a string")
    elif not title:
        raise ValueError("title should not be empty")
    if not (namespace is None or isinstance(namespace, str)):
        raise TypeError("namespace must be a string")
    if not (parent_title is None or isinstance(parent_title, str)):
        raise TypeError("parent_title must be a string")

    return f"{parent_title} / {title}" if parent_title else (f"{namespace} :: {title}" if namespace else title)


def default_failure_callback(name: str, error: Exception) -> None: ...


def dict_to_chainable(model: dict) -> Chainable: ...


def list_to_chainable(model: Union[tuple, list]) -> Chainable: ...


