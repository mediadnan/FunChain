from fastchain import Chain
from statistics import mode, mean, median
from components import split


chain = Chain(
    split(','),
    ('*', int),
    {
        'max': max,
        'min': min,
        'mode': mode,
        'mean': (mean, round),
        'median': median,
    },
    title='branching_test'
)


if __name__ == '__main__':
    result = chain("1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6")
    assert result == {'max': 9, 'min': 0, 'mode': 1, 'mean': 3, 'median': 2}
