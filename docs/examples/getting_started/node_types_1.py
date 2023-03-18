import re
from fastchain import node

URL_PATTERN = re.compile(r'(([a-zA-Z]+:)?//)?(\w+\.)+(\w+)(/.)*?')



def add_https_scheme(url: str) -> str:
    if not isinstance(url, str):
        raise TypeError("Invalid url type")
    elif not URL_PATTERN.match(url):
        raise ValueError("Invalid url value")
    *_, url = url.rpartition('//')
    return f'https://{url}'


url_node = node(add_https_scheme)



if __name__ == '__main__':

    print(add_https_scheme('mediadnan.com'))
    print(add_https_scheme('//mediadnan.com'))
    print(add_https_scheme('http://mediadnan.com?login=adnan'))
    print(add_https_scheme('https://mediadnan.com/path/to'))
    print(add_https_scheme('git://mediadnan.com'))

