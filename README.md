<div align="center" id="heading">
  <h1><img src="./docs/_static/favicon/favicon.svg" alt="logo" width="24" height="24" /> FunChain</h1>
  <strong style="">chain functions easily and safely</strong>
  <div>
    <br/>
    <a href="https://github.com/mediadnan/funchain/actions/workflows/tests.yml"><img src="https://github.com/mediadnan/funchain/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
    <img src="https://img.shields.io/github/license/mediadnan/funchain" alt="License MIT" />
    <a href="https://fast-chain.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/fast-chain" alt="Read the Docs"></a>
    <img src="https://img.shields.io/pypi/pyversions/funchain" alt="Python versions" />
    <img src="https://img.shields.io/pypi/v/funchain" alt="PyPI version" />
    <img src="https://img.shields.io/pypi/dm/funchain" alt="PyPI - Downloads"/>
  </div>
</div> 


## Introduction
**FunChain** is a package that provides tools and utilities to easily compose functions sequentially
to create processing pipelines with minimum code and simple syntax *(such as OR operator ``func1 | func2``)*,
all while tracking, reporting and containing any crash that could occur in any step.  

The library was part of another API client project and was developed to reduce boilerplate code when dealing
with networking and unstructured responses, after that and due to its general purpose usage, it was separated 
into an independent library that could be integrated in other python projects.

**FunChain** is now based on another standalone library called [Failures](https://pypi.org/project/failures/)
that only specialises in labeling and reporting nested errors.

## Installation
You can include ``FunChain`` into your environment using this command

````shell
pip install funchain
````

## Audience
Anyone working on a python project that requires processing data through multiple functions and needs to isolate
each step and report errors with labels and details **can** benefit from the tooling offered by this library,
using it may reduce boilerplate code and code repetition.

Continue reading the documentation to find out if ``FunChain`` offers tools that you need 
or aligns with your design pattern.

## Features
### Composing functions sequentially 🔗
Composing functions in a sequence to create a pipeline
is the **main functionality** of this library, the sequence
of functions *(or so-called nodes)* results in a single
function-like objects that passes the result of one function
to the next as input.

The sequential composition ***(or piping)*** can be done 
using the ``|`` operator, like; ``seq = fun1 | fun2 | fun3``

### Iterating multiple items ⛓️
While composing functions, we might want to apply a function
to each item of an iterable instead of applying it to the whole
iterable; this is achieved using the ``*`` operator,
Like: ``seq = fun1 * fun2``.

If ``fun1`` returns a list like
``[1, 2, 3]`` the next one will be called like 
``[fun2(1), fun2(2), fun2(3)]`` instead of ``fun2([1, 2, 3])``
if we used ``fun1 | fun2``

### Branching 🦑
When a returned value needs to take multiple routes at some points,
we can use branching methods, and that by defining the structure
of the result and _(either a ``dict`` and ``list``)_ filling it
with the sequence of functions, and the result will have the same 
structure.

If we want to extract a dictionary from a given input,
we can do it like ``fun1 | {'a': fun2, 'b': fun3 | fun4}``,
so if ``fun1`` returns ``5``, the result will be 
``{'a': fun(5), 'b': fun4(fun3(5))}``.

The same if we need a list as a result, we can define 
the structure to be ``fun1 | [fun2, fun3 | fun4]``,
that way the result will be ``[fun(5), fun4(fun3(5))]``

### Debug friendly 🪲
Composing multiple functions makes it hard
to traceback errors and get which input caused it,
especially in production where it's hard to reproduce 
the same crash or debug it.
But thanks to the ``failures`` library, tracking and pinpointing 
nested errors becomes way easier; each exception gets wrapped
and labeled with a qualified name indicating its location, and
the exact input that caused it.

### Good and minimal syntax 🎈
The syntax of this library was intentionally made easy and minimal users to compose functions,
to achieve complex pipeline structures with the least amount of code, and make it more readable and intuitive
to be easily maintained. It also makes it a beginner-friendly tool with a gentle learning.

### Async support 🪄
All the previously mentioned features are available for asynchronous
operations; coroutines can be composed together the same way to produce
an asynchronous chain of functions,
the same if a normal function is piped to an async one.

This makes ``funchain`` a good choice for processing IO intensive
operations, such as performing network requests or reading files from
the hard drive in a non-blocking way.

## Usage

In these example we will only scratch the surface to get and idea,
to learn more about FunChain please visit the [documentation page](https://fast-chain.readthedocs.io/en/latest/)

Consider that we want a function that takes a string with comma separated numbers 
then returns the square roots of each number rounded to 2 decimal places,
this process can be decomposed to the following steps:
1. Splitting the values by commas
2. Parsing each string number to float *(stripping is automatically handled by builtin `float`)*
3. Calculating the square root of each number
4. Round the numbers to 2 decimal places
5. Return a list of those numbers

> **Note**
> Of course this is too simple to be practical and only serves as example.

This can be easily implemented like so

````python
from math import sqrt

def rounded_square_roots(numbers: str) -> list[float]:
    return [round(sqrt(float(number)), 2) for number in numbers.split(',')]
````

One line of code with a list comprehension and nested function composition, it works wonderful if we try it

````pycon
>>> rounded_square_roots('523.5814, 74.2347, 366.3606, 418.3412, 134.8182')
[22.88, 8.62, 19.14, 20.45, 11.61]
````

But now let's try this

````pycon
>>> rounded_square_roots(None)
Traceback (most recent call last):
...
AttributeError: 'NoneType' object has no attribute 'split'
````

This was expected of course because None has method named split, 
maybe we can refactor our function to handle this

````python
from math import sqrt

def rounded_square_roots(numbers: str) -> list[float]:
  if not isinstance(numbers, str):
    return []
  return [round(sqrt(float(number)), 2) for number in numbers.split(',')]
````

Now if a user provide inappropriate data type *(namely `str`)*, an empty list will be returned
and problem solved right? well not quite yet, consider dealing with this input

````pycon
>>> rounded_square_roots('im_a_number, 74.2347, 366.3606')
Traceback (most recent call last):
...
ValueError: could not convert string to float: 'im_a_number'
````

Okay no big deal, we can further improve the function, maybe add logging too to get an idea about what happening

````python
from math import sqrt
from logging import getLogger

logger = getLogger('rounded_square_roots')

def rounded_square_roots(numbers: str) -> list[float]:
  result = list()
  if not isinstance(numbers, str):
    logger.error(f"Operation failed, expected {str} but got {type(numbers)}")
    return result
  for number in numbers.split(','):
    try:
      float_number = float(number)
    except ValueError as error:
      logger.error(f"An element was skipped because {error!r} was raised")
    else:
      result.append(round(sqrt(float_number), 2))
  return result
````

That will handle the previous issue, let's test it

````pycon
>>> rounded_square_roots('im_a_number, 74.2347, 366.3606')
An element was skipped because ValueError("could not convert string to float: 'im_a_number'") was raised
[8.62, 19.14]
````

Now what about this one

````pycon
>>> rounded_square_roots('im_a_number, -74.2347, 366.3606')
An element was skipped because ValueError("could not convert string to float: 'im_a_number'") was raised
Traceback (most recent call last):
...
ValueError: math domain error
````

I think we see where this is going, adding more try...except blocks, more loggings and what if we want to add 
a function that remotely report those failures to notify the team about those errors... 
This is not scalable and can become ugly very quickly,
it is already too much work for a function supposed to do a simple task like this.

### Solution
We see now that the previous steps need to be isolated and safely handled, this can be automated because it's a clear
and constant repetitive pattern, and that where we can use ``funchain.Chain`` to that can automate this task for us.

chains are defined globally with a name and a set of small functions that define the processing steps,
those functions will be the chain's nodes and composed automatically and safely.

for this example we will also need a utility function ``funchain.chainable`` to partially apply shared arguments
*(similar to ``functools.partial`` with some additional functionalities)*

The new code will look like this

````python
from math import sqrt
from funchain import Chain, node_maker

rounded_square_roots = Chain(
    "rounded_square_roots",
    node_maker(str.split, sep=',', default_factory=list),
    '*',
    (float, sqrt, node_maker(round, ndigits=2)),
    list
)
````

Now let's understand each argument given to `Chain`

+ `"rounded_square_roots"`: is the name of our chain, used to identify it in reports in particular.
+ `chainable(str.split, sep=',', default_factory=list)`: wraps the `str.split` descriptor to partially pass 
  a keyword argument and return a new emtpy list in case of failure.
+ `'*'`: is an option, and it informs the chain that the next node should iterate over all the items instead of the
  entire input as a whole.
+ `(float, sqrt, chainable(round, ndigits=2))`: are 3 nodes grouped together into deeper layer (think of it as nested chain),
  and the reason is for `'*'` to take them all as a block for iteration, otherwise only `float` will iterate the results.  
+ `list`: is needed after `'*'` as this option is lazy and returns a generator that need to be evaluated.
  *This is an optimization feature for dealing with lager datasets and not a limitation*.

Now it's time to test our chain

````pycon
>>> rounded_square_roots('523.5814, 74.2347, 366.3606, 418.3412, 134.8182')
[22.88, 8.62, 19.14, 20.45, 11.61]
````

But to reveal a bit of what happens behind the scenes, we can print stats to the standard output
by passing an additional keyword argument to the constructor ``print_stats=True``, the code will look like this

````python
from math import sqrt
from funchain import Chain, node_maker

rounded_square_roots = Chain(
    "rounded_square_roots",
    node_maker(str.split, sep=',', default_factory=list),
    '*',
    (float, sqrt, node_maker(round, ndigits=2)),
    list,
    print_stats=True
)
````

Let's run our code again

````pycon
>>> results = rounded_square_roots('523.5814, 74.2347, 366.3606, 418.3412, 134.8182')
-- STATS -----------------------------
   success percentage:        100%
   successful operations:     17
   unsuccessful operations:   0
   unreached nodes:           0
   required nodes:            5
   total number of nodes:     5
--------------------------------------
>>> results
[22.88, 8.62, 19.14, 20.45, 11.61]
````

When trying to pass a bad input type:

````pycon
>>> result = rounded_square_roots(None)
-- STATS -----------------------------
   success percentage:        0%
   successful operations:     0
   unsuccessful operations:   1
   unreached nodes:           4
   required nodes:            5
   total number of nodes:     5
--------------------------------------
rounded_square_roots/sequence[0]/str.split raised TypeError("descriptor 'split' for 'str' objects doesn't apply to a 'NoneType' object") when receiving <class 'NoneType'>: None
>>> result
[]
````

Trying to break the second node y passing none-numeric value

````pycon
>>> result = rounded_square_roots('im_a_number, 74.2347, 366.3606')
-- STATS -----------------------------
   success percentage:        93%
   successful operations:     8
   unsuccessful operations:   1
   unreached nodes:           0
   required nodes:            5
   total number of nodes:     5
--------------------------------------
rounded_square_roots/sequence[1]/sequence[0]/float raised ValueError("could not convert string to float: 'im_a_number'") when receiving <class 'str'>: 'im_a_number'

>>> result
[8.62, 19.14]
````

Or trying to calculate the square root of a negative number

````pycon
>>> result = rounded_square_roots('im_a_number, -74.2347, 366.3606')
-- STATS -----------------------------
   success percentage:        83%
   successful operations:     6
   unsuccessful operations:   2
   unreached nodes:           0
   required nodes:            5
   total number of nodes:     5
--------------------------------------
rounded_square_roots/sequence[1]/sequence[0]/float raised ValueError("could not convert string to float: 'im_a_number'") when receiving <class 'str'>: 'im_a_number'
rounded_square_roots/sequence[1]/sequence[1]/sqrt raised ValueError('math domain error') when receiving <class 'float'>: -74.2347

>>> result
[19.14]
````
It's all handled and the program is still running, note that a healthy branch is not impacted by other exceptions
and did make it to the end``[19.14]``, and the errors logged are pointing out directly to source of failure
with its absolute location and name.

# Maintainers
- [MARSO Adnan](https://github.com/mediadnan) *(author)*
