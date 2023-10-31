# Getting started

## Using ``chain()``
The main utility provided by `funchain` is [``chain()``](#funchain.chain),
this function is used to compose functions and compile them to a ready 
to use function-like object.

This function acts like a smart constructor that generates a specific `funchain` node,
this objects can be called _like a function_ with a single argument, and passes the
result of one function to the next, then returns the last function's result as result.

Let's consider these two python functions :

````python
def increment(num: int) -> int:
    return num + 1

def double(num: int) -> int:
    return num * 2
````

We can create a simple chain like this:

````python
from funchain import chain

calculate = chain(increment, double, increment)
````

Now ``calculate`` is a function that increments a number, then doubles it and then increments
it again; So if we try it we will get this

````pycon
>>> calculate(5)    # ((5 + 1) * 2) + 1
13
>>> calculate(8)    # ((8 + 1) * 2) + 1
19
>>> calculate(-2)   # ((-2 + 1) * 2) + 1
-1
````

This same functionality can be achieved simply by writing
````python
calculate = lambda num: increment(double(increment(num)))
````
Or
````python
def calculate(num: int) -> int:
    num = increment(num)
    num = double(num)
    return increment(num)
````
However, there some key differences about this approach and the 
one with ``chain()``, and one of them is containing errors inside the function.

````pycon
>>> calculate = lambda num: increment(double(increment(num)))
>>> calculate(None)
Traceback (most recent call last):
    ...
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
>>> calculate = chain(increment, double, increment)
>>> calculate(None)  # None

````
This **doesn't** mean that errors are completely ignored, but they can be retrieved
and collected if a <a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.Reporter" target="_blank">Reporter [⮩]</a>

{emphasize-lines="9,13"}
````python
from funchain import chain, Reporter

def increment(num: int) -> int:
    return num + 1

def double(num: int) -> int:
    return num * 2

calculate = chain(increment, double, increment, name="calculate")

if __name__ == "__main__":
    reporter = Reporter("my_pipeline")
    result = calculate(None, reporter)
    print(f"Result: {result!r}", f"Failures: {reporter.failures[0]}", sep="\n")
````

``reporter.failures`` is a list of reported failures registered throughout the
input processing, here our reporter reported one detailed failure

``Failure(source='my_pipeline.calculate.increment', error=TypeError("unsupported operand type(s) for +: 'NoneType' and 'int'"), details={'input': None})``

These failures can be later handled. For more information about handling failures
check the <a href="https://failures.readthedocs.io" target="_blank"><b>Failures</b> [⮩]</a>
library.
