# Chain types

## Predefined nodes
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

chain = inc + dbl + dbl

if __name__ == "__main__":
    print("The result of process is : ", chain(5))
    # The result of process is :  24
    # Because : ((5 + 1) * 2) * 2 == 24
````

Beyond the ability to compose nodes using the ``+`` operator (which is elegant 😍), 
the ``node()`` function offers to rename its functions with a meaningful name that will be used in reports in case of failure;

take ``lambda`` functions as example:

````pycon
>>> from funchain import node, Reporter
>>> inc = node(lambda x: x+1, name="increment")
>>> dbl = node(lambda x: x*2, name="double")
>>> fun = dbl + inc + dbl
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
If we didn't specify the name, the failure source would be ``err_node_1.lambda``
## Input iteration
...TODO

## Combining chains
...TODO

