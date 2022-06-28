from fastchain import Chain
from components import tag, split, join


pipeline = Chain(
    (
        split(),
        '*',
        str.strip,
        tag('p'),
    ),
    join(),
    tag('div'),
    title='nested_html',
)

if __name__ == '__main__':
    print(pipeline("text-1 text-2 text-3"))
