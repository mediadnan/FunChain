from pytest import mark, raises
from fastchain import chains
from copy import deepcopy


@mark.parametrize("name, result", [
    (None, []),
    ('chain', ['chain']),
    ('my_chain2', ['my_chain2']),
    ('awsome-chain', ['awsome-chain']),
    ('group.chain', ['group', 'chain']),
    ('my_category.sub_category.chain', ['my_category', 'sub_category', 'chain']),
], ids=repr)
def test_split_name(name, result):
    assert chains._split_name(name) == result


@mark.parametrize("name, Error, msg", [
    (object(), TypeError, "The name must be string"),
    (b"my_chain", TypeError, "The name must be string"),
], ids=repr)
def test_split_name_validation(name, Error, msg):
    with raises(Error, match=msg):
        chains._split_name(name)  # noqa


@mark.parametrize("names, Error, msg", [
    ([], ValueError, "The name cannot be empty"),
    ([""], ValueError, "'' is not a valid name"),
    (["_my_chain"], ValueError, "'_my_chain' is not a valid name"),
    (["my", "", "chain"], ValueError, "'' is not a valid name"),
    (["my chain"], ValueError, "'my chain' is not a valid name"),
    (["my/chain"], ValueError, "'my/chain' is not a valid name"),
    (["my:chain"], ValueError, "'my:chain' is not a valid name"),
    (["my[chain]"], ValueError, r"'my\[chain\]' is not a valid name"),
    ([" my_chain "], ValueError, "' my_chain ' is not a valid name"),
], ids=repr)
def test_validate_names(names, Error, msg):
    with raises(Error, match=msg):
        chains._validate_names(names)


CHAIN1, CHAIN2, CHAIN3 = object(), object(), object()
REGISTRY = {'chain': CHAIN1, 'sub': {'chain': CHAIN2, 'sub': {'chain': CHAIN3}}}


@mark.parametrize('names, result', [
    ([], REGISTRY),
    ([""], None),
    (["chain"], CHAIN1),
    (["sub"], REGISTRY['sub']),
    (["nothing"], None),
    (["sub", "sub"], REGISTRY['sub']['sub']),
    (["sub", "chain"], CHAIN2),
    (["sub", "nothing"], None),
    (["sub", "sub", "chain"], CHAIN3),
    (["sub", "sub", "sub", "chain"], None),
])
def test_get_by_name(names, result):
    assert chains._get_by_name(names, REGISTRY) is result


@mark.parametrize("registry, result", [
    (REGISTRY, [CHAIN1, CHAIN2, CHAIN3]),
    (REGISTRY['chain'], [CHAIN1]),
    (REGISTRY['sub'], [CHAIN2, CHAIN3]),
    (REGISTRY['sub']['chain'], [CHAIN2]),
    (REGISTRY['sub']['sub'], [CHAIN3]),
    (REGISTRY['sub']['sub']['chain'], [CHAIN3]),
])
def test_get_registry_chains(registry, result):
    assert chains._get_components(registry) == result


@mark.parametrize("names, chain, result, Error, msg", [
    ([""], )
])
def test_register(names, chain, result, Error, msg):
    reg = deepcopy(REGISTRY)
    if Error is not None:
        with raises(Error, match=msg):
            ...
    else:
        

