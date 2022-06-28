import re
from typing import AnyStr, Callable, List
from fastchain import funfact


@funfact
def regex(pattern: AnyStr, flags: re.RegexFlag = re.DOTALL) -> Callable[[str], List[str]]:
    """generates a function that matches a regular expression and returns those matches"""
    def _regex(text: str) -> List[str]:
        matches = regex_pattern.findall(text)
        if not matches:
            # This makes sure the chain does proceed
            # if no matches where found.
            raise ValueError(f"No matches for {pattern!r}")
        return matches
    regex_pattern = re.compile(pattern, flags)
    return _regex


@funfact
def split(char: str = ' ') -> Callable[[str], List[str]]:
    def _split(text: str) -> List[str]:
        """splits `char`-separated values string into a list of strings"""
        return text.split(char)
    return _split


@funfact
def join(char: str = '') -> Callable[[List[str]], str]:
    def _join(texts: List[str]) -> str:
        """joins a list of strings using `char` into a single string"""
        return char.join(texts)
    return _join


@funfact
def tag(tag_name: str):
    """encloses the text between tags"""
    def _tag(text: str) -> str:
        return f"<{tag_name}>{text}</{tag_name}>"
    return _tag
