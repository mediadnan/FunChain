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
 ... TODO