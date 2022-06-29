from fastchain import Chain
from components import join, split, tag


chain = Chain(
    split(),
    ('*', str.strip, tag('p')),
    join(),
    tag('div'),
    title='nested_html',
)

if __name__ == '__main__':
    assert chain("text1 text2 text3") == "<div><p>text1</p><p>text2</p><p>text3</p></div>"
