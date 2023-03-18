from typing import overload, Callable


from .nodes import (
    build, async_build, is_node_async,
    Input, Output, AsyncCallable,
    DictGroupChainable, ListGroupChainable, AsyncDictGroupChainable, AsyncListGroupChainable,
    BaseNode, Node, AsyncNode, Chain, DictGroup, ListGroup,
    AsyncDictGroup, AsyncListGroup,
    ModelType, Model
)
from .reporter import Reporter, Severity
from .util.annotation import is_typed_optional


@overload
def node() -> Chain[Input, Input]: ...
@overload
def node(function: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def node(function: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def node(function: AsyncCallable[Input, Output]) -> AsyncNode[Input, Output]: ...
@overload
def node(function: Callable[[Input], Output]) -> Node[Input, Output]: ...
@overload
def node(structure: AsyncDictGroupChainable[Input]) -> AsyncDictGroup[Input]: ...
@overload
def node(structure: AsyncListGroupChainable[Input]) -> AsyncListGroup[Input]: ...
@overload
def node(structure: DictGroupChainable[Input]) -> DictGroup[Input]: ...
@overload
def node(structure: ListGroupChainable[Input]) -> ListGroup[Input]: ...


def node(obj=None) -> BaseNode:
    """Makes a chainable node from the given object"""
    if obj is None:
        return Chain()
    if is_node_async(obj):
        return async_build(obj)
    return build(obj)

#
# class Model:
#     _data: Input
#     _reporter: Reporter
#     __model_name__: str
#
#     def __init__(self, data: Input, reporter: Reporter):
#         self._data = data
#         self._reporter = reporter(self.__class__.__model_name__)
#
#     def __init_subclass__(cls, **kwargs):
#         for name, attr in cls.__dict__.items():
#             if not isinstance(attr, BaseNode) or name.startswith('_'):
#                 continue
#             annotation = cls.__annotations__.get(name)
#             if annotation and is_typed_optional(annotation):
#                 attr = attr.optional()
#             setattr(cls, name, _node_to_getter(name, attr))
#         if '__model_name__' not in cls.__dict__:
#             setattr(cls, '__model_name__', cls.__qualname__)
#


def _node_to_getter(name: str, nd: BaseNode):
    """binds the node to the bot as a property"""
    def getter(self: Model):
        result = nd.process(self._data, self._reporter(name, severity=nd.severity))
        try:
            # caching the result for the next call
            self.__dict__[name] = result
        except AttributeError:
            # for objects with __slots__ and no __dict__
            pass
        return result
    return property(getter, doc=f'gets {name!r} (readonly)')

#
# def model(cls: type) -> ModelType:
#     annotations = dict(cls.__annotations__)
#     attrs = {}
#     for name, attr in cls.__dict__.items():
#         if isinstance(attr, BaseNode) and not name.startswith('_'):
#             if (annotation := annotations.get(name)) and is_typed_optional(annotation):
#                 attr = attr.optional()
#             attr = _node_to_getter(name, attr)
#         attrs[name] = attr
#     attrs['__model_name__'] = cls.__dict__.get('__model_name__', cls.__qualname__)
#     return type(cls.__name__, (*cls.__bases__, Model), attrs)
#

# @model
class MyModel(Model):
    upper: node(str) | str.upper
    lower: node(str) | str.lower


my_chain = node() * MyModel
