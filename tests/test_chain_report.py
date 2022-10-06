from pytest import mark
from fastchain import make


class Handler:
    def __init__(self):
        self.called = False

    def __call__(self, *args, **kwargs):
        self.called = True


@mark.parametrize("func, always, called", [
    ("increment", True, True),
    ("increment", False, False),
    ("fail", True, True),
    ("fail", False, True),
])
def test_chain_add_report_handler(func, always, called, increment, fail):
    handler = Handler()
    chain = make(eval(func))
    chain.clear_report_handlers()
    chain.add_report_handler(handler, always)
    chain(2)
    assert handler.called is called
