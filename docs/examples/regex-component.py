import re
from fastchain import funfact


@funfact(name="regex.findall", default_factory=list)
def regex_findall(pattern: str, flags: int = re.DOTALL):
    # this block is executed at definition
    def func(text: str) -> list[str]:
        # this block is executed at usage
        return compiled_pattern.findall(text)
    compiled_pattern = re.compile(pattern, flags)
    return func
