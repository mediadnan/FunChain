from pytest import mark, raises
from fastchain import chains


def func(*_, **__):
    """does nothing"""


# test name validation  -------------------------------------------------------------------------------------------------
@mark.parametrize('name, Error, message', [
    (object(), TypeError, "The name must be str"),
    (b"my_chain", TypeError, "The name must be str"),
    (None, ValueError, "The name cannot be empty"),
    ("", ValueError, "'' is not a valid name"),
    ("_my_chain", ValueError, "'_my_chain' is not a valid name"),
    ("my..chain", ValueError, "'' is not a valid name"),
    ("my chain", ValueError, "'my chain' is not a valid name"),
    ("my/chain", ValueError, "'my/chain' is not a valid name"),
    ("my:chain", ValueError, "'my:chain' is not a valid name"),
    ("my[chain]", ValueError, r"'my\[chain\]' is not a valid name"),
    (" my_chain ", ValueError, "' my_chain ' is not a valid name"),
], ids=repr)
def test_name_processing_validation(name, Error, message, increment):
    with raises(Error, match=message):
        chains.make(func, name=name)


@mark.parametrize('name, result', [
    ('chain', ['chain']),
    ('my_chain2', ['my_chain2']),
    ('awsome-chain', ['awsome-chain']),
    ('group.chain', ['group', 'chain']),
    ('my_category.sub_category.chain', ['my_category', 'sub_category', 'chain']),
], ids=repr)
def test_validate_name_allowed_names(name, result):
    chain = chains.make(func, name=name) == result
    assert chain in chains.get()
