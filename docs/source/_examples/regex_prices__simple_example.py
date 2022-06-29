from fastchain import Chain
from components import regex, split


chain = Chain(
    regex(r'\$\s?(\d+\.?\d*)', title="match_prices"),
    ('*', float),
    list,
    title="match_prices"
)

if __name__ == '__main__':
    result = chain("They have a 34% off this week, the initial price was $70.28 now it's $52.45")
    assert result == [70.28, 52.45], f"{result = }"
