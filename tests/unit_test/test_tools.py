import pytest

from fastchain import _tools as tools


class TestValidateName:
    """
       Testing name validation with validate_name()
       this function must validate name for chains primarily
       by checking the type and preventing empty strings
       and usage of reserved characters : / . [ ]
       and for future probable title features
       the function must only accept names that:
           - start with a letter (case-insensitive) or _
           - contain more than one character
           - only contain letter, digits, _ and - characters
    """
    @pytest.mark.parametrize('name', [None, 6, object()])
    def test_type_validation(self, name):
        with pytest.raises(TypeError):
            tools.validate_name(name)  # type: ignore[tools.validate_name]

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
            tools.validate_name(name)

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
        assert tools.validate_name(name) is name
