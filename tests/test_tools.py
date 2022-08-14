import pytest
import inspect
from fastchain import _tools as tools  # noqa


@pytest.mark.parametrize('name, result', [
    ("ClassName", "class_name"),
    ("Class12Name", "class12_name"),
    ("_ClassName", "_class_name"),
    # add more cases here ...
])
def test_camel_to_snake_function(name, result):
    assert tools.camel_to_snake(name) == result


class Object:
    pass


class ObjectWithFakeAdd:
    def add(self, a, b):
        raise NotImplementedError


@pytest.mark.parametrize('name_variation, expected_name', [
    pytest.param((), 'add', id='no method name provided'),
    pytest.param(('add',), 'add', id='explicit add name provided'),
    pytest.param(('sum', ), 'sum', id='custom name provided')
])
@pytest.mark.parametrize('ObjectClass', [Object, ObjectWithFakeAdd])
def test_bind_method(ObjectClass, name_variation, expected_name):
    def add(self, a, b):
        return a + b
    assert not hasattr(add, '__self__')
    obj = ObjectClass()
    tools.bind(obj, add, *name_variation)
    method = getattr(obj, expected_name)  # type: ignore
    assert inspect.ismethod(method)
    assert hasattr(method, '__self__')
    assert method(3, 5) == 8
