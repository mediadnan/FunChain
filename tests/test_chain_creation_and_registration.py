"""Collection of tests about the chain creation and validation"""
from pytest import mark, raises, param
import fastchain


def func(*_, **__):
    """Useless function"""


@mark.parametrize('name, Error, message', [
    (object(), TypeError, "The name must be str"),
    (b"my_chain", TypeError, "The name must be str"),
    ("", ValueError, "The name cannot be empty"),
    ("_my_chain", ValueError, "'_my_chain' is not a valid name"),
    ("my..chain", ValueError, "'' is not a valid name"),
    ("my chain", ValueError, "'my chain' is not a valid name"),
    ("my/chain", ValueError, "'my/chain' is not a valid name"),
    ("my:chain", ValueError, "'my:chain' is not a valid name"),
    ("my[chain]", ValueError, r"'my\[chain\]' is not a valid name"),
    (" my_chain ", ValueError, "' my_chain ' is not a valid name"),
])
def test_chain_naming_validation(name, Error, message, mock_registry):
    """Tests preventing bad chain names"""
    with raises(Error, match=message):
        fastchain.make(func, name=name)


@mark.parametrize('args, Error, message', [
    ((), ValueError, "Cannot create an empty sequence"),
    ((object(),), TypeError, "Unsupported type object"),
    ((...,), ValueError, "Cannot create an empty sequence"),
    (('?',), ValueError, "Cannot create an empty sequence"),
    (('?', func), ValueError, "Cannot create a chain with only optional nodes"),
    (('?', '*', func), ValueError, "Cannot create a chain with only optional nodes"),
    (('*', '?', func), ValueError, "Cannot create a chain with only optional nodes"),
    (('&', func), ValueError, "Unknown options '&'"),
    (([],), ValueError, "Cannot create an empty model"),
    (({},), ValueError, "Cannot create an empty model"),
    ((fastchain.match(),), ValueError, "Cannot create an empty match"),
    ((fastchain.match(func),), ValueError, "Cannot create a match with a single branch"),
])
def test_core_validation(args, Error, message, mock_registry):
    with raises(Error, match=message):
        fastchain.make(*args)


@mark.parametrize("name, msg", [
    ('sub', "The name 'sub' is already registered"),
    ('sub.sub', "The name 'sub.sub' is already registered"),
    ('sub.sub.chain', "The name 'sub.sub.chain' is already registered"),
])
def test_double_registration(name, msg, mock_registry):
    """Test preventing chain double registration or override"""
    fastchain.make(func, name='sub.sub.chain')
    with raises(ValueError, match=msg):
        fastchain.make(func, name=name)


@mark.parametrize("name, expected_name", [
    (None, 'unregistered'),
    ('my_chain', 'my_chain'),
    ('my-chain_01', 'my-chain_01'),
    ('category.my_chain', 'category.my_chain'),
])
@mark.parametrize("args, expected_length, required", [
    param("(func,)", 1, 1, id="single function"),
    param("(func, func)", 2, 2, id="sequence of two functions"),
    param("(func, '?', func)", 2, 1, id="sequence a required function and an optional function"),
    param("(func, '*', '?', func)", 2, 1, id="sequence with loop then optional applied"),
    param("(func, '?', '*', func)", 2, 1, id="sequence with optional then loop applied"),
    param("(func, '*', func, func)", 3, 3, id="sequence with an iteration option"),
    param("(func, '?', (func, func), func)", 4, 2, id="sequence with an iteration option"),
    param("([func, func],)", 2, 2, id="list model with two functions"),
    param("([func, ('?', func)],)", 2, 1, id="list model with two functions with optional branch"),
    param("({'key0': func, 'key1': func},)", 2, 2, id="dict model with two functions"),
    param("({'key0': func, 'key1': ('?', func)},)", 2, 1, id="dict model with two functions with optional branch"),
    param("(fastchain.match(func, func),)", 2, 2, id="match with two functions"),
    param("(fastchain.chainable(func),)", 1, 1, id="chainable"),
])
def test_chain_creation(args: str, name, expected_name, expected_length, required, mock_registry):
    chain = fastchain.make(*eval(args), name=name)
    cls = type(chain).__name__
    assert isinstance(chain, fastchain.chains.Chain)
    assert chain.name == expected_name
    assert len(chain) == expected_length
    assert repr(chain) == f'{cls}(name={expected_name!r}, nodes/required={expected_length}/{required})'


def test_chain_registration_and_retrieve(mock_registry):
    """Test chain global registration and retrieving"""
    fastchain.make(func)                                    # unregistered because it wasn't named
    fastchain.make(func, name="free", register=False)       # explicitly unregistered
    chain0 = fastchain.make(func, name="chain")             # registered without category
    chain1 = fastchain.make(func, name="sub.chain")         # registered under sub category
    chain2 = fastchain.make(func, name="sub.sub.chain1")    # registered under sub sub-category
    chain3 = fastchain.make(func, name="sub.sub.chain2")    # registered under the same sub sub-category

    assert fastchain.get() == [chain0, chain1, chain2, chain3]
    assert fastchain.get("chain") == [chain0]
    assert fastchain.get("sub") == [chain1, chain2, chain3]
    assert fastchain.get("sub.chain") == [chain1]
    assert fastchain.get("sub.sub") == [chain2, chain3]
    assert fastchain.get("sub.sub.chain1") == [chain2]
    assert fastchain.get("sub.sub.chain2") == [chain3]
