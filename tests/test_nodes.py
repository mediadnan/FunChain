import pytest

from fastchain.nodes import *
from fastchain.options import optional, set_default  # noqa: needed for eval()


# Testing node creation and validation
#   Leaf nodes

def test_pass_functionality(reporter):
    node = Pass()
    assert isinstance(node, Node)
    assert node.name == "pass"
    assert node.title == "pass"
    assert node.optional is False
    assert repr(node) == "<Pass 'pass'>"


@pytest.mark.parametrize(
    "function, name, Error, msg", [
        (object(), None, TypeError, "function must be callable"),
        (lambda x: x + 1, object(), TypeError, "name must be str"),
    ]
)
def test_chainable_validation(function, name, Error, msg):
    with pytest.raises(Error, match=msg):
        Chainable(function, name)


class Func:
    def __init__(self, *_): pass

    def __call__(self, *_): pass

    def method(self, *_): pass

    @classmethod
    def class_method(cls, *_): pass

    @staticmethod
    def static_method(*_): pass


def func(*_):
    def _func(*_): pass

    return _func


@pytest.mark.parametrize(
    "function, expected_name", [
        pytest.param(func, 'func', id="normal function"),
        pytest.param(func(), 'func.<locals>._func', id="inner function"),
        pytest.param(Func, 'Func', id="class constructor"),
        pytest.param(Func(), 'Func', id="callable object"),
        pytest.param(Func.method, 'Func.method', id="class method"),
        pytest.param(Func().method, 'Func.method', id="object method"),
        pytest.param(Func.class_method, 'Func.class_method', id="class class_method"),
        pytest.param(Func.static_method, 'Func.static_method', id="class staticmethod"),
        pytest.param(lambda *_: None, '<lambda>', id="lambda function")
    ]
)
def test_chainable_creation_default_name(function: Callable, expected_name: str):
    node = Chainable(function)
    assert node.core is function
    assert node.name is expected_name
    assert node.title is expected_name
    assert node.optional is False
    assert repr(node) == f"<Chainable '{expected_name}'>"


def test_chainable_creation_custom_name():
    custom_name = "custom_name"
    node = Chainable(func, custom_name)
    assert node.name is custom_name
    assert node.title is custom_name
    assert node.optional is False
    assert isinstance(node, Node)
    assert repr(node) == "<Chainable 'custom_name'>"


@pytest.fixture
def node_list(increment) -> list[Node]:
    return [Chainable(increment, f'inc{i + 1}') for i in range(3)]


@pytest.fixture
def node_dict(node_list) -> dict[str, Node]:
    return {node.name: node for node in node_list}


#   Node groups
@pytest.mark.parametrize("NodeSequenceType", [Sequence, ListModel, Match])
@pytest.mark.parametrize("nodes, name, Error, msg", [
    ("None", None, TypeError, f"nodes must be a list of {Node} objects"),
    ("[None,]", None, TypeError, f"nodes must be a list of {Node} objects"),
    ("[]", None, ValueError, "Cannot create an empty"),
    ("node_list", object(), TypeError, "name must be str")
])
def test_common_node_sequence_creation_validation(NodeSequenceType, nodes, name, Error, msg, node_list):
    with pytest.raises(Error, match=msg):
        NodeSequenceType(eval(nodes), name)


@pytest.mark.parametrize("NodeSequenceType, nodes, name, Error, msg", [
    (Sequence, "list(map(optional, node_list))", None, ValueError, "At least one node must be required"),
    (Match, "[node_list[0],]", None, ValueError, "should at least contain two branches")
])
def test_specific_node_sequence_creation_validation(NodeSequenceType, node_list, nodes, name, Error, msg):
    with pytest.raises(Error, match=msg):
        NodeSequenceType(eval(nodes), name)


@pytest.mark.parametrize("NodeMappingType", [DictModel])
@pytest.mark.parametrize("nodes, name, Error, msg", [
    ("None", None, TypeError, f"nodes must be a dict mapping keys to {Node} objects"),
    ("{'key': None}", None, TypeError, f"nodes must be a dict mapping keys to {Node} objects"),
    ("{}", None, ValueError, "Cannot create an empty"),
    ("node_dict", object(), TypeError, "name must be str")
])
def test_common_node_mapping_creation_validation(NodeMappingType, nodes, name, Error, msg, node_dict):
    with pytest.raises(Error, match=msg):
        NodeMappingType(eval(nodes), name)


@pytest.mark.parametrize("NodeSequenceType, default_name", [
    (ListModel, "model"),
    (Sequence, "sequence"),
    (Match, "match"),
])
def test_common_node_sequence_creation(NodeSequenceType, default_name, node_list):
    node = NodeSequenceType(node_list)
    assert isinstance(node, Node)
    assert isinstance(node, NodeSequence)
    assert node.name == default_name
    assert node.title == default_name
    assert repr(node) == f"<{NodeSequenceType.__name__} '{default_name}'>"
    assert node.core == node_list
    assert all(a == b for a, b in zip(node.nodes, node_list))
    assert all(a == b for a, b in zip(node.branches, enumerate(node_list)))


@pytest.mark.parametrize("NodeMappingType, default_name", [(DictModel, "model")])
def test_common_node_mapping_creation(NodeMappingType, default_name, node_dict):
    node = NodeMappingType(node_dict)
    assert isinstance(node, Node)
    assert isinstance(node, NodeMapping)
    assert node.name == default_name
    assert node.title == default_name
    assert repr(node) == f"<{NodeMappingType.__name__} '{default_name}'>"
    assert node.core == node_dict
    assert all(a == b for a, b in zip(node.nodes, node_dict.values()))
    assert all(a == b for a, b in zip(node.branches, node_dict.items()))


#   Node wrappers
@pytest.mark.parametrize("NodeWrapperType", [Loop])
@pytest.mark.parametrize("node, Error, msg", [
    ("object()", TypeError, f"only wraps {Node} instances"),
])
def test_node_wrapper_creation_validation(NodeWrapperType, node, Error, msg, node_list):
    with pytest.raises(Error, match=msg):
        NodeWrapperType(eval(node))


@pytest.mark.parametrize("NodeWrapperType", [Loop])
@pytest.mark.parametrize("node_code", [
    "node_list[0]",
    "Sequence(node_list)",
    "ListModel(node_list)",
    "DictModel(node_dict)",
    "Match(node_list)",
    "NodeWrapperType(node_list[0])"
])
def test_node_wrapper_creation(NodeWrapperType, node_code, node_dict, node_list):
    node: Node = eval(node_code)
    wrapper = NodeWrapperType(node)
    assert wrapper.core is node
    assert wrapper.name is node.name
    assert repr(wrapper) == f"<{NodeWrapperType.__name__} '{node.name}'>"


# Test node default values
@pytest.mark.parametrize("node_code, default", [
    ("node_list[0]", None),
    ("Pass()", None),
    ("Sequence(node_list)", None),
    ("ListModel([Chainable(func), optional(Chainable(func))])", [None]),
    ("DictModel({'k1': Chainable(func), 'k2': optional(Chainable(func))})", {"k1": None}),
    ("Match(node_list)", [None, None, None]),
])
def test_node_default(node_code, default, node_list, node_dict):
    node: Node = eval(node_code)
    assert node.default() == default


# Test node expose
def test_passive_node_expose():
    node = Pass()
    assert node.expose == {}


def test_chainable_expose():
    node = Chainable(func)
    assert node.expose == {node: True}
    node.optional = True
    assert node.expose == {node: False}


@pytest.mark.parametrize("req_comp", [
    (True, True, True),
    (True, True, False),
    (True, False, False),
    (False, False, False),
], ids=repr)
@pytest.mark.parametrize("NodeGroupType", [
    Sequence,
    ListModel,
    DictModel,
    Match
])
def test_node_group_expose(NodeGroupType, req_comp: tuple[bool, bool, bool], node_list, node_dict):
    node: NodeGroup = NodeGroupType(node_list if issubclass(NodeGroupType, NodeSequence) else node_dict)
    node_req = tuple(zip(node.nodes, req_comp, strict=True))
    for node_, required_ in node_req:
        node_.optional = not required_
    assert node.expose == dict(node_req)
    node.optional = True
    assert node.expose == dict(zip(node_list, (False, False, False), strict=True))


@pytest.mark.parametrize("NodeWrapperType", [Loop])
def test_wrapper_expose(NodeWrapperType):
    wrapper: NodeWrapper = NodeWrapperType(Chainable(func))



# Test setting title
set_title_composition = [(), ('root',), ('root', 'branch')]


@pytest.mark.parametrize("composition", set_title_composition, ids=lambda x: f"set_title{repr(x)}")
def test_pass_ignores_set_title(composition):
    node = Pass()
    title = node.title
    node.set_title(*composition)  # noqa
    assert node.title == title


@pytest.mark.parametrize("composition, title", zip(
    set_title_composition,
    ("func", "root.func", "root[branch].func")
), ids=repr)
def test_chainable_set_title(composition, title):
    node = Chainable(func, "func")
    node.set_title(*composition)  # noqa
    assert node.title == title


@pytest.mark.parametrize("composition, title", zip(set_title_composition, ["group", "root.group", "root[branch].group"]))
@pytest.mark.parametrize("NodeGroupType", [Sequence, ListModel, DictModel, Match])
def test_node_group_set_title(NodeGroupType, composition, title, node_list, node_dict):
    group = NodeGroupType(node_list if issubclass(NodeGroupType, NodeSequence) else node_dict, "group")
    group.set_title(*composition)  # noqa
    assert group.title == title
    for branch, node in group.branches:
        assert node.title == f"{title}[{branch}].{node.name}"


@pytest.mark.parametrize("composition, title", zip(
    set_title_composition,
    ("func", "root.func", "root[branch].func")
), ids=repr)
@pytest.mark.parametrize("NodeWrapperType", [Loop])
def test_node_wrapper_set_title(NodeWrapperType, composition, title):
    wrapper = NodeWrapperType(Chainable(func))
    wrapper.set_title(*composition)  # noqa
    assert wrapper.title == wrapper.core.title == title


# Test successful node executions
def test_pass_exec(reporter):
    node = Pass()
    inp = object()
    success, result = node(inp, reporter)
    assert success is True
    assert result is inp
    assert not reporter.counter
    assert not reporter.failures


@pytest.mark.parametrize("inp, out, mark, failures", [
    (2, (True, 3), [0, 1], False),
    (None, (False, None), [1, 0], True),
])
def test_chainable_exec(increment, reporter, inp, out, mark, failures):
    node = Chainable(increment)
    assert node(inp, reporter) == out
    assert bool(reporter.failures) is failures
    assert reporter.counter[node] == mark


@pytest.mark.parametrize("sequence_code, out", [
    ("[Chainable(increment), Chainable(increment)]", (True, 5)),
    ("[Chainable(fail), Chainable(increment)]", (False, None)),
    ("[Chainable(increment), Chainable(fail)]", (False, None)),
    ("[Chainable(increment), optional(Chainable(fail))]", (True, 4)),
    ("[optional(Chainable(fail)), Chainable(increment)]", (True, 4)),
    ("[Chainable(increment), set_default(Chainable(fail), default=0)]", (False, 0)),
    ("[Chainable(increment), set_default(Chainable(fail), default_factory=list)]", (False, [])),
], ids=repr)
def test_sequence_exec(sequence_code, out, increment, fail, reporter):
    sequence = Sequence(eval(sequence_code))
    assert sequence(3, reporter) == out


@pytest.mark.parametrize("list_model_code, out", [
    ("[Chainable(increment), Chainable(increment)]", (True, [4, 4])),
    ("[Chainable(fail), Chainable(increment)]", (False, [None, 4])),
    ("[Chainable(increment), Chainable(fail)]", (False, [4, None])),
    ("[Chainable(increment), optional(Chainable(fail))]", (True, [4])),
    ("[optional(Chainable(fail)), Chainable(increment)]", (True, [4])),
    ("[Chainable(increment), set_default(Chainable(fail), default=0)]", (False, [4, 0])),
    ("[Chainable(increment), set_default(Chainable(fail), default_factory=list)]", (False, [4, []])),
], ids=repr)
def test_list_model_exec(list_model_code, out, increment, fail, reporter):
    model = ListModel(eval(list_model_code))
    assert model(3, reporter) == out


@pytest.mark.parametrize("dict_model_code, out", [
    ("{'a': Chainable(increment), 'b': Chainable(increment)}", (True, {'a': 4, 'b': 4})),
    ("{'a': Chainable(fail), 'b': Chainable(increment)}", (False, {'a': None, 'b': 4})),
    ("{'a': Chainable(increment), 'b': Chainable(fail)}", (False, {'a': 4, 'b': None})),
    ("{'a': Chainable(increment), 'b': optional(Chainable(fail))}", (True, {'a': 4})),
    ("{'a': optional(Chainable(fail)), 'b': Chainable(increment)}", (True, {'b': 4})),
    ("{'a': Chainable(increment), 'b': set_default(Chainable(fail), default=0)}", (False, {'a': 4, 'b': 0})),
    ("{'a': Chainable(increment), 'b': set_default(Chainable(fail), default_factory=list)}", (False, {'a': 4, 'b': []})),
], ids=repr)
def test_dict_model_exec(dict_model_code, out, increment, fail, reporter):
    model = DictModel(eval(dict_model_code))
    assert model(3, reporter) == out


@pytest.mark.parametrize("match_code, out", [
    ("[Chainable(increment), Chainable(increment)]", (True, [4, 5])),
    ("[Chainable(fail), Chainable(increment)]", (False, [None, 5])),
    ("[Chainable(increment), Chainable(fail)]", (False, [4, None])),
    ("[Chainable(increment), optional(Chainable(fail))]", (False, [4, None])),
    ("[optional(Chainable(fail)), Chainable(increment)]", (False, [None, 5])),
    ("[Chainable(increment), set_default(Chainable(fail), default=0)]", (False, [4, 0])),
    ("[Chainable(increment), set_default(Chainable(fail), default_factory=list)]", (False, [4, []])),
], ids=repr)
def test_dict_model_exec(match_code, out, increment, fail, reporter):
    match = Match(eval(match_code))
    default = list(node.default() for node in match.nodes)
    assert match(None, reporter) == (False, default)  # noqa
    assert match((2, 3, 4), reporter) == (False, default)
    assert match((3, 4), reporter) == out


@pytest.mark.parametrize("node, out", [
    ("Chainable(double)", [8, 10]),
    ("Sequence([Chainable(double), Chainable(double)])", [16, 20]),
    ("ListModel([Chainable(double), Chainable(double)])", [[8, 8], [10, 10]])
], ids=repr)
def test_loop_exec(node, out, double, reporter):
    loop = Loop(eval(node))
    success, result = loop([4, 5], reporter)
    assert success is True
    assert list(result) == out
