import pytest
from fastchain import chains


# Chain functionalities -------------------------------------------------------------------------------------------------

class CallableObj:
    def __call__(self, arg): return [arg]


@pytest.mark.parametrize("body, length, input, output", [
    # single function setups
    ("increment,", 1, 3, 4),
    ("lambda x: x - 1,", 1, 4, 3),
    ("float,", 1, "4", 4.0),
    ("round,", 1, 4.143, 4),
    ("str,", 1, 4, '4'),
    ("tuple,", 1, 'abc', ('a', 'b', 'c')),
    ("CallableObj(),", 1, 4, [4]),
    ("chainable(double),", 1, 5, 10),
    ("chainable(lambda x, y: x + y, 2, name='add_two'),", 1, 3, 5),

    # tuple of chainables setups
    ("increment, double", 2, 6, 14),
    ("(((increment, double),),),", 2, 6, 14),
    ("increment, double, increment", 3, 2, 7),
    ("increment, (double, increment)", 3, 2, 7),
    ("double, {'di': increment, 'dd': double}", 3, 2, {"di": 5, "dd": 8}),
    ("double, [increment, double]", 3, 2, [5, 8]),

    # list of chainables setups
    ("[increment],", 2, 6, [7]),
    ("[increment, double],", 2, 6, [7, 12]),
    ("[..., double],", 1, 2, [2, 4]),
    ("[[increment, double], {'i': increment, 'd': double}, (increment, double)],", 6, 2, [[3, 4], {'i': 3, 'd': 4}, 6]),

    # dict of chainables setups
    ("{'d': double},", 1, 3, {'d': 6}),
    ("{'d': double, 'i': increment},", 2, 3, {'d': 6, 'i': 4}),
    ("{'d': double, 'pass': ...},", 1, 3, {'d': 6, 'pass': 3}),
    ("{'b1': (double, increment, [double, increment]), 'b2': increment},", 5, 3, {'b1': [14, 8], 'b2': 4}),

    # match group
    ("match(increment, double), ", 2, [2, 2], (3, 4)),
    ("dict.items, '*', match(str, (increment, double)), dict", 4, {1: 1, 2: 2}, {'1': 4, '2': 6}),
])
def test_input_output(body, input, output, increment, double, length, mock_registry):
    chain = chains.make('test', *eval(body))
    assert repr(chain) == "<chain 'test'>"
    assert len(chain)
    res = chain(input)
    assert res == output


# Chain configuration ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('lf_kwargs, failures_logged', [
        (dict(), True),
        (dict(log_failures=True), True),
        (dict(log_failures=False), False),
], ids=[
    "log_failures=default",
    "log_failures=True",
    "log_failures=False"
])
@pytest.mark.parametrize('ps_kwargs, stats_printed', [
        (dict(), False),
        (dict(print_stats=True), True),
        (dict(print_stats=False), False),
], ids=["print_stats=default",
        "print_stats=True",
        "print_stats=False"])
@pytest.mark.parametrize('logger_kwargs, logger', [
        (dict(), 'fastchain'),
        (dict(logger='test_logger'), 'test_logger'),
        (dict(logger=logging.getLogger('test_logger')), 'test_logger'),
], ids=["logger=default",
        "logger=test_logger'",
        "logger=getLogger('test_logger')"])
@pytest.mark.parametrize('chain_creation', [
    "Chain('failing_chain', fail, **kwargs)",
    "ChainGroup('group', **kwargs)('failing_chain', fail)"
], ids=["from Chain",
        "from ChainGroup"])
def test_configuration_logger(
        caplog,
        capfd,
        chain_creation,
        fail,
        logger_kwargs,
        logger,
        lf_kwargs,
        failures_logged,
        ps_kwargs,
        stats_printed
):
    kwargs = logger_kwargs | lf_kwargs | ps_kwargs  # noqa: kwargs is used in eval
    chain = eval(chain_creation)
    with caplog.at_level(0):
        chain(None)
    if not failures_logged:
        assert not caplog.records
    else:
        last_record = caplog.records[-1]
        assert last_record.name == logger
        assert ('-- STATS --' in capfd.readouterr().out) is stats_printed


# Report handling -------------------------------------------------------------------------------------------------------

class ReportHandler:
    called: bool
    def __init__(self): self.called = False
    def __call__(self, *args, **kwargs): self.called = True


@pytest.mark.parametrize('always', [True, False], ids=['always', 'failures_only'])
def test_chain_add_handler(double, always):
    handler = ReportHandler()
    chain = Chain('test', double, log_failures=False)
    chain.add_report_handler(handler, always)
    chain(2)
    if always:
        assert handler.called
        handler.called = False
    else:
        assert not handler.called
    chain(None)
    assert handler.called


def test_chain_group_add_handler(fail):
    group = ChainGroup('group', log_failures=False)
    chains = [group(f'chain{i}', fail) for i in range(1, 4)]
    handler = ReportHandler()
    group.add_report_handler(handler)
    for chain in chains:
        chain(None)
        assert handler.called
        handler.called = False


# Chain Groups ----------------------------------------------------------------------------------------------------------

def test_chain_group_registered_chains(increment):
    group = ChainGroup('group')
    chain = group('my_chain', increment)
    assert 'my_chain' in group
    assert group['my_chain'] is chain
    with pytest.raises(ValueError, match='already been registered'):
        group('my_chain', increment)
    with pytest.raises(KeyError, match='no chain is registered with the name'):
        _ = group['unregistered_chain']
