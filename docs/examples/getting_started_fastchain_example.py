import re
import math
from functools import partial
from fastchain import chain

NUMBERS_RE = re.compile(r'[+-]?(\d+(\.\d*)?|\.\d+)')

find_square_root = chain(
    NUMBERS_RE.search,
    re.Match.group,
    float,
    math.sqrt,
    partial(round, ndigits=2),
    str
)
