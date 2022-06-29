from fastchain import Chain
from components import regex, split


chain = Chain(
    {
        'prices': (regex(r'\$\s?(\d+\.?\d*)', title="match_prices"), '*', float),
        'words': (split(), len),
        'parts': (split(','), '*', str.strip, str.title)
    },
    title='analyse_comment',
)

if __name__ == '__main__':
    assert chain("They have a 34% off this week, the initial price was $70.28 now it's $52.45") == \
           {
               'prices': (70.28, 52.45),
               'words': 15,
               'parts': (
                   'They Have A 34% Off This Week',
                   "The Initial Price Was $70.28 Now It'S $52.45"
               )
           }
