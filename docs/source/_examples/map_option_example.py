from fastchain import Chain
from components import split


chain = Chain(
    split(),
    '*',
    float,
    abs,
    round,
    title="abs_rounded_values",
)

if __name__ == '__main__':
    result = chain("-134.76 103.4 -89.34")
    assert result == (135, 103, 89), f"the value was {result}"
