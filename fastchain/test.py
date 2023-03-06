import re
import inspect
from fastchain._util import get_varname  # noqa


class Object:
    var_name: str | None

    def __init__(self, stack_level=2):
        # self.var_name = get_var_name()
        self.var_name = get_varname(stack_level)
        print(self.var_name)


main = Object()
# another = Object()
#
#

class MyObj:
    parse = Object()

    class Inner:
        parse = Object()

    def func(self):
        return Object()

obj = MyObj().func()
