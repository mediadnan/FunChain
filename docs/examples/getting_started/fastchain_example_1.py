import re
import math
from fastchain import node

NUMBERS_RE = re.compile(r'[+-]?(\d+(\.\d*)?|\.\d+)')

find_square_root = node(NUMBERS_RE.search) | re.Match.group | float | math.sqrt | node(round, ndigits=2) | str

