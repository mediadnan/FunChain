from math import sqrt
from fastchain import Chain

chain = Chain(float, sqrt, round, title='rounded_square_root', callback=print)

if __name__ == '__main__':
    result = chain("   17  ")
    assert result == 4
    assert isinstance(result, int)
