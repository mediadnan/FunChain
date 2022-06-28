from fastchain import Chain, chainable
from components import split_by_commas

abs_rounded_values = Chain(
    split_by_commas,
    '*',
    float,
    abs,
    round,
    title="abs_rounded_values"
)

if __name__ == '__main__':
    result = abs_rounded_values("-134.76, 103.4 , -89.34")
    assert result == (135, 103, 89)
