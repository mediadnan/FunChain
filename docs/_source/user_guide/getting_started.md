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
````

This same functionality can be achieved simply by writing
````python
calculate = lambda num: increment(double(increment(num)))
````
However, there are some key differences between this approach and the 
one with ``chain()``, and one the main differences is containing errors.

````pycon
>>> increment(double(increment(None)))
Traceback (most recent call last):
    ...
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
>>> calculate = chain(increment, double, increment)
>>> calculate(None)  # None

````

The chain operates internally based on the railway pattern, it isolates each node and breaks the chain in case 
of failure; The process can be visualized like this:

```{mermaid}
flowchart LR
    I((input)) --> A
    A[fun1] -->|ok| B
    A --> |error| X
    B[fun2] --> |ok| C[fun3]
    B --> |error| X
    C --> E((output))
    C --> |error| X
    X((None))
```

The chain object don't raise an exception, it returns ``None`` as alternative result if any of it nodes fail,
but this **doesn't** mean that errors are completely ignored,
they can be retrieved if a <a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.Reporter" target="_blank">Reporter [⮩]</a>
object is passed after the input argument, that reporter can be later reviewed and properly handled.

## Reporting failures
To gather execution failures from a chain, we will pass a ``Reporter`` object to ``calculate``

{emphasize-lines="4"}
````pycon
>>> from failures import Reporter
>>> # or (from funchain import Reporter) same...
>>> reporter = Reporter("calculate")
>>> calculate(None, reporter)

>>> failure = reporter.failures[0]
>>> failure.source
'calculate.increment'
>>> failure.error
TypeError("unsupported operand type(s) for +: 'NoneType' and 'int'")
>>> failure.details
{'input': None}
````
``reporter.failures`` is a list of reported failures, in this case we only have 1,
the error was reported with the label ``'calculate.increment'`` that reveals its location,
and the input that caused it, which is ``None``.

```{important}
It is **highly recommended** to pass reporters to `funchain` chains and nodes,
especially in production, otherwise the errors will be permanently silenced.
```

```{important}
The functions used as ``funchain`` components should be **pure** functions with a single positional argument,
the function should not **mutate** the input.
```