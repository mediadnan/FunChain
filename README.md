<div align="center" id="heading">
  <h1><img src="./docs/_static/favicon/favicon.svg" alt="logo" width="24" height="24" /> FunChain</h1>
  <strong style="">chain functions easily and safely</strong>
  <div>
    <br/>
    <a href="https://github.com/mediadnan/funchain/actions/workflows/tests.yml"><img src="https://github.com/mediadnan/funchain/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
    <a href="https://codecov.io/gh/mediadnan/FunChain" ><img src="https://codecov.io/gh/mediadnan/FunChain/graph/badge.svg?token=HZWUDTLC3O"/></a>
    <img src="https://img.shields.io/github/license/mediadnan/funchain" alt="License MIT" />
    <a href="https://funchain.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/funchain" alt="Read the Docs"></a>
    <img src="https://img.shields.io/pypi/pyversions/funchain" alt="Python versions" />
    <img src="https://img.shields.io/pypi/v/funchain" alt="PyPI version" />
    <img src="https://img.shields.io/pypi/dm/funchain" alt="PyPI - Downloads"/>
  </div>
</div> 


## Introduction
**FunChain** is a package that provides tools and utilities to easily compose functions sequentially
to create processing pipelines with minimum code and simple syntax,
all while tracking, reporting and containing any crash that could occur in any step.  

The library was part of another API client project and was developed to reduce boilerplate code when dealing
with networking and unstructured responses, after that and due to its general purpose usage, it was separated 
into an independent library that could be integrated in other python projects.

**FunChain** is now based on another standalone library called [Failures](https://pypi.org/project/failures/)
that only specialises in labeling and reporting nested errors.

> **_NOTE_** This library is still in **experimentation** phase, 
> if you plan to include it in your production app, make sure
> to test that use case to avoid any unexpected bugs.


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

This means `fun1 ➜ fun2 ➜ fun3`, or programmatically speaking
`fun3(fun2(fun1(input)))`

### Iterating multiple items ⛓️
While composing functions, we might want to apply a function
to each item of an iterable instead of applying it to the whole
iterable, for example if ``fun1`` returns a list like ``[1, 2, 3]`` 
the next one will be called like ``[fun2(1), fun2(2), fun2(3)]`` 
instead of ``fun2([1, 2, 3])``

This means `fun1 ⭄ fun2`, or programmatically speaking 
`[fun2(item) for item in fun1(input)]`

### Branching 🦑
When a returned value needs to take multiple routes at some points,
we can use branching methods, and that by defining the structure
of the result and _(either a ``dict`` and ``list``)_ filling it
with the sequence of functions, and the result will have the same 
structure.

So for dictionaries, the model `{'a': fun1, 'b': fun2}` will return
`{'a': fun1(input), 'b': fun2(input)}`

And the model `[fun1, fun2]` will return `[fun1(input), fun2(input)]`.

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
to be easily maintained. It also makes it a beginner-friendly tool with a gentle learning curve.

### Async support 🪄
All the previously mentioned features are available for asynchronous
operations; coroutines can be composed together the same way to produce
an asynchronous chain of functions,
the same if a normal function is piped to an async one.

Normal and asynchronous functions can be mixed together and
`funchain` will know what to do, and if any async function is chained,
the result will automatically be an asynchronous callable.

This makes this library a good choice for processing IO intensive
operations, such as performing network requests or reading files from
the hard drive in a non-blocking way.

### Flexibility
The structure of a function chain can be as deep and complex as needed,
every component is considered a chain node, so a chain can contain a
dict or list model and each can contain another chain or model and so.

## Usage
### Function chaining

This example illustrates how to compose functions in a sequence
using `chain()`

```python
>>> from funchain import chain

>>> def add_two(num: int) -> int:
...   return num + 2

>>> def double(num: int) -> int:
...   return num * 2

>>> fun = chain(add_two, double, add_two)

>>> fun(5)
16
```
In this example we created two simple functions `add_two` and `double`
and we chained them `chain(add_two, double, add_two)`.

This basically means that any input given to `fun` _which is a chain_,
will be incremented by 2, then doubled, then incremented again by 2;

This mean: `add_two(5) = 7 ⮕ double(7) = 14 ⮕ add_two(14) = 16`

### Predefined nodes
We can compile nodes in advance using `node()` and chain them later
by concatenation _(using_ `+` _operator)_

```python
>>> from funchain import node

>>> add_two = node(lambda x: x + 2, name="add_two")

>>> double = node(lambda x: x * 2, name="double")

>>> fun = add_two | double | add_two

>>> fun(5)
16
```

This works the same as the first example and it's more convenient for functions that are meant to be used
as components.

If we had a functions like the previous example,
we can integrate compile it to a node like this

```python
>>> from funchain import node

>>> def double(num: int) -> int:
...   return num * 2

>>> nd = node(double)

>>> fun = nd | nd

>>> fun(5)
20
```


_... TODO_