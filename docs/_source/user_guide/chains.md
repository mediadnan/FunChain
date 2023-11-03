# Funchain Nodes
``funchain`` has several functions to build nodes _(the building blocks of chains)_, those functions compile down
to a function like object that takes an input value, and optionally a ``Reporter`` object.

In this chapter, we will see some of those functions like ``chain()``, ``node()`` and ``loop()``...

## Reusable nodes
Using ``chain()`` is the most straight forward to compose functions, so if we want to chain functions
sequentially the syntax is ``chain(fun1, fun2, func3)``, that will be mathematically equivalent to ``fun3(fun2(fun1(x)))``.

However, there is another way to prepare nodes _(functions that can be composed)_ previously using [node()](#funchain.node);
this function takes a single positional argument that should be a function _(or a callable)_ and compiles
it into a funchain component; those components can be later composed to make new function chains.

{caption="node_test.py" emphasize-lines="12"}
````python
from funchain import node

def increment(num: int) -> int:
    return num + 1

def double(num: int) -> int:
    return num * 2

inc = node(increment)
dbl = node(double)

chain = inc | dbl | dbl

if __name__ == "__main__":
    print("The result of process is : ", chain(5))
    # The result of process is :  24
    # Because : ((5 + 1) * 2) * 2 == 24
````

Beyond the ability to compose nodes using the ``|`` operator (which is elegant 😍), 
the ``node()`` function offers to rename its functions with a meaningful name that will be used in reports in case of failure;

take ``lambda`` functions as example:

````pycon
>>> from funchain import node, Reporter
>>> inc = node(lambda x: x+1, name="increment")
>>> dbl = node(lambda x: x*2, name="double")
>>> fun = dbl | inc | dbl
>>> fun(3)
14
>>> reporter = Reporter("err_node_1")
>>> fun(None, reporter)

>>> reporter.failures
[Failure(source='err_node_1.double', error=TypeError("unsupported operand type(s) for *: 'NoneType' and 'int'"), details={'input': None})]
>>> reporter = Reporter("err_node_2")
>>> fun([3], reporter)

>>> reporter.failures
[Failure(source='err_node_2.increment', error=TypeError('can only concatenate list (not "int") to list'), details={'input': [3, 3]})] 
````
If we didn't specify the name, the failure source would be ``err_node_1.lambda``.

```{note}
By default, the node takes the function's name _(or ``__name__`` to be specific)_
 as a label to be used in reports.

But if a custom name is provided, it must meet a specific criteria, for more information check the reporter's
<a href="https://failures.readthedocs.io/en/latest/guide/reporting.html#naming-conventions" target="_blank">naming convension [⮩]</a>.
```

The node itself can be called without being chained, all type of nodes have the same
call interface that is ``node(argument: Any, /, reporter: Reporter = None) -> Any``

```pycon
>>> from funchain import node, Reporter
>>> add_two = node(lambda x: x+2, name="add_two")
>>> add_two(5)
7
>>> reporter = Reporter("my_operation")
>>> add_two(None, reporter)

>>> reporter.failures
[Failure(source='my_operation.add_two', error=TypeError("unsupported operand type(s) for +: 'NoneType' and 'int'"), details={'input': None})]
```

## Partial arguments
As previously mentioned, functions that can be chained must ave a single input argument, or in general have multiple
arguments but at most only one required first argument, and at least must take at least one argument.

But if a function takes more than one argument, some of them can be partially applied:
```pycon
>>> from funchain import node
>>> def add(a: int, b: int) -> int:
...     return a + b
>>> add_two = node(add).partial(b=2)
>>> add_five = node(add).partial(b=5)
>>> op_chain = add_two | add_five | node(add).partial(10) # add 10
>>> op_chain(4) # 4 + 2 + 5 + 10
21
```
In this case, and while both arguments `a` and `b` are required, it is mandatory to apply `.partial()` method.

```{note}
The ``.partial()`` only uses the builtin
 <a href="https://docs.python.org/3/library/functools.html#functools.partial" target="_blank">``functools.partial`` [⮩]</a>
 under the hood.
```

## Input iteration
Imagine that a function returns a list, tuple or any iterable object, and we want to chain it to the next function to it

````pycon
>>> from funchain import node
>>> def get_next_three(a: int) -> tuple[int, int, int]:
...     return a + 1, a + 2, a + 3
>>> double = node(lambda x: x*2, name="double")
>>> process = node(get_next_three) | double
>>> process(4)
(5, 6, 7, 5, 6, 7)
````
This gets the next three numbers of 4 ``(5, 6, 7)``
and then double the entire result resulting in ``(5, 6, 7, 5, 6, 7)``

If we need to double each element of that set of numbers instead of doubling the entire tuple, we can achieve this like
follows

{emphasize-lines="1"}
````pycon
>>> process = node(get_next_three) * double
>>> process(4)
[10, 12, 14]
````
This time `double` gets applied to each item of that sequence instead of the whole tuple as we have seen in the previous
example.

The `*` operator indicates that the next node will receive an iterable object
and should be applied to each of its elements.

The same can be achieved with `chain()` and [`loop()`](#funchain.loop) together

````pycon
>>> from funchain import chain, loop
>>> def get_next_three(a: int) -> tuple[int, int, int]:
...     return a + 1, a + 2, a + 3
>>> def double(a):
...     return a * 2
>>> process = chain(get_next_three, loop(double))
>>> process(4)
[10, 12, 14]
````

## Combining chains
...TODO

