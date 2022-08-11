import pytest
import inspect
from fastchain import _tools as tools  # noqa


class TestValidateName:
    """
       Testing name validation with validate_name()
       this function must validate name for chains primarily
       by checking the type and preventing empty strings
       and usage of reserved characters : / . [ ]
       and for future probable coll_title features
       the function must only accept names that:
           - start with a letter (case-insensitive) or _
           - contain more than one character
           - only contain letter, digits, _ and - characters
    """
    @pytest.mark.parametrize('name', [None, 6, object()])
    def test_type_validation(self, name):
        with pytest.raises(TypeError):
            tools.validate_chain_name(name)  # type: ignore[tools.validate_name]

    @pytest.mark.parametrize('name', [
        '',
        'a',
        '-my_chain',
        '1chain',
        'my chain',
        'my.chain',
        'my/chain',
        'my:chain',
        'my[chain]',
        ' my_chain '
    ])
    def test_forbidden_names(self, name):
        with pytest.raises(ValueError):
            tools.validate_chain_name(name)

    @pytest.mark.parametrize('name', [
        'ca',
        'c1',
        'c_',
        'my-chain',
        'my_chain',
        'my_12chain',
        '__my_chain',
        '___my_chain',
    ])
    def test_validate_name_allowed_names(self, name):
        assert tools.validate_chain_name(name) is name


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
