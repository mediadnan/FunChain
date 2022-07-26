<div align="center" id="heading">
  <h1><img src="./docs/_static/favicon/favicon-light.svg" alt="logo" width="24" height="24" /> FastChain</h1>
  <strong style="">chain functions easily and safely</strong>
  <div>
    <br/>
    <a href="https://github.com/mediadnan/fastchain/actions/workflows/tests.yml"><img src="https://github.com/mediadnan/fastchain/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
    <img src="https://img.shields.io/github/license/mediadnan/fastchain" alt="License MIT" />
    <a href="https://fast-chain.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/fast-chain" alt="Read the Docs"></a>
    <img src="https://img.shields.io/pypi/pyversions/fastchain" alt="Python versions" />
    <img src="https://img.shields.io/pypi/v/fastchain" alt="PyPI version" />
    <img src="https://img.shields.io/pypi/dm/fastchain" alt="PyPI - Downloads"/>
  </div>
</div> 


## Introduction

FastChain is a python3 developers' tool aiming to ease piping functions by passing results from a function
to another safely in a fault-tolerant way, fast, and make reports after each execution.

It does not only provide a way of chaining functions sequentially (**piping**) 
which was the original intention, 
but also provide ways of **branching** *(passing a result to multiple sequences simultaneously)*,
**iterating** *(passing each item of an iterable result to the next function or sequence, something like 'map')*,
**matching** *(passing each item of an iterable result to a corresponding sequence, something like 'strict zip')*,
and **skipping** by making a part of a structure optional and passing its input to the next if it fails.

The goal of this project is to reduce some boilerplate code needed for safely processing any type of data,
like handling exceptions *(nested try...except blocks)*, checking results and make decisions *(nested if...else blocks)*,
report processing statistics and pinpointing the exact source of the failure and its reason easing the debugging process,
the reports are designed to answering questions like 
'how many operations have succeeded or failed?', 'how many required components have succeeded or failed?',
'which is the exact component that failed?', 'what is the exception risen?', 
'what is the value that caused this failure?', and more...

### Philosophy
FastChain is intentionally simple by design, and it's made to be a tool not a framework,
and that's for the following reasons:

- **Beginner-friendly**: by making it easy to be learned and used by everyone in the great python community,
  staying as close as possible to the regular pythonic syntax (*gentle learning curve*). 
  In fact, this project is typed and type-checked so users receive IDE support and warnings when working with it. 
- **Integrability**: by making it easily integrable with other frameworks and libraries the user is already familiar with,
  and add it as a light tool and why not an extension for one of your favorite frameworks.
- **Cohesiveness**: do only what it's expected to do, and do it very well (*single-responsibility principle*). 
  At first, it was tempting to create an events based system where a user can hook handlers to specific signals
  like failures, only to realize after how overly engineered that would've been,
  adding unnecessary complexity. Instead, functionalities like those
  can be optionally create by the user or handled by third party libraries.
- **Independency**: by being simple and specialized, FastChain doesn't need too many functionalities that can 
  be provided by other third party libraries currently, so it only depends on python's standard libraries.

As well, FastChain is designed to be robust and keep the following standards:

- **Performance**: by being as optimized as possible to minimize the impact of added functionality over
  the original performance as if it was implemented without FastChain, and for this reason consider the following;
  **chains** are designed *(and supposed)* to be defined globally and be used as functions.
  So the impact of initialization only happen once your program is run and be ready for usage
  (low-latency use in favour of cold-starts).
  With that in mind, it is not optimized to use it in systems that start your program each time their called. 
- **Abstraction**: by offering a declarative and intuitive api, the user specifies the structure of the process flow,
  and FastChain takes care of how it will be processed, hiding away the complexity and implementation details.
- **Isolation**: running each function in isolation and capture error without breaking other components, or breaking
  the main program. Briefly, if a function raises an exception,
  it will be recorded and inform the next chain functions that it failed.
- **Monitoring**: being able to keep track of how many functions (nodes) have succeeded after each call
  and tell how many were supposed to succeed, record errors, the input that caused them to fail, and the component's
  identifier. to automate monitoring the execution behaviour and call specific handlers for specific conditions,
  reducing the debugging effort.

And finally, it's supposed to give it users the following benefits:

- **Decoupling**: by installing it, the package will obviously be globally available in your project,
  so most of the functionality needed will be imported from it *(site-package)* 
  instead of creating module for those functionalities and import it all over your code. 
  And in the other hand, FastChain also provides a way of creating reusable custom components, so you can define them
  in one place and use them everywhere.
- **DRY**: as previously mentioned, handling errors, checking results, logging, analysing and reporting everywhere
  in your code can be tedious and can become ugly very quickly, 
  so having a tool that automates that for you can be handy, especially if the projects changes or scales
  which brings us to the next benefit.
- **Scalability**: process flows can be modified or redesigned a lot easier which makes your project
  easier to grow (quickly, easily and safely) compared if you have to handle everything manually.
- **Flexibility**: chains can be created, modified or redefined with less to worry about introducing bugs 
  and with less energy and time compared to what it would've been.
- **Support & Maintenance**: The project is actively maintained and constantly patched, updated and optimized. 
  And I'm the number one consumer, knowing that I rely on it in my other projects.

### Audience
This project is targeting python developers in general, and developers that do any kind of data processing in particular.


## Installation
It is of course recommended that you install FastChain in a virtual environment for each project instead of installing
it globally.
### Install from pypi
You can install the last pypi release via this command
````shell
pip install fastchain
````
Check that you have the last version installed, by running this command
````shell
pip show fastchain
````
### Get source code
FastChain is actively developed on GitHub, you can get the latest instance
directly from the repository via this command:
````shell
pip install git+https://github.com/mediadnan/fastchain.git#egg=fastchain
````

## Usage
This is only a surface scratching example to give you an idea about the package, 
for more information please visit the [documentation page](https://fast-chain.readthedocs.io/en/latest/)

In this example we will create a simple chain *(pipeline)* that takes a string 
containing comma-separated number and returns the rounded square root of each number.

This process can be decomposed to the following steps:
1. Splitting the values by commas
2. Parse each string number to float
3. Calculate the square root of each number
4. Round the numbers to 2 decimal places
5. Return a list of those numbers

> **Note**
> This too simple to be practical, and only serves as example.

This can be hardcoded of course like so:

````python
from math import sqrt

def rounded_square_roots(numbers: str) -> list[float]:
    return [round(sqrt(float(number)), 2) for number in numbers.split(',')]
````
Easy of course, it works wonderful if we try it:
````pycon
>>> rounded_square_roots('523.5814, 74.2347, 366.3606, 418.3412, 134.8182')
[22.88, 8.62, 19.14, 20.45, 11.61]
````
Now try this:
````pycon
>>> rounded_square_roots(None)
Traceback (most recent call last):
...
AttributeError: 'NoneType' object has no attribute 'split'
````
Maybe we can refactor our function to become like this:
````python
from math import sqrt

def rounded_square_roots(numbers: str) -> list[float]:
  if not isinstance(numbers, str):
    return []
  return [round(sqrt(float(number)), 2) for number in numbers.split(',')]
````
Problem solved, right? well imagine dealing with this input:
````pycon
>>> rounded_square_roots('im_a_number, 74.2347, 366.3606')
Traceback (most recent call last):
...
ValueError: could not convert string to float: 'im_a_number'
````
Okay we can further improve the function, maybe add logging too:
````python
from math import sqrt
from logging import getLogger

logger = getLogger('rounded_square_roots')

def rounded_square_roots(numbers: str) -> list[float]:
  result = list()
  if not isinstance(numbers, str):
    return result
  for number in numbers.split(','):
    try:
      float_number = float(number)
    except ValueError as error:
      logger.error(f"Operation failed with {error!r}")
    else:
      result.append(round(sqrt(float_number), 2))
  return result
````
Let's test it:
````pycon
>>> rounded_square_roots('im_a_number, 74.2347, 366.3606')
Operation failed with ValueError("could not convert string to float: 'im_a_number'")
[8.62, 19.14]
````
Perfect! but what about this:
````pycon
>>> rounded_square_roots('im_a_number, -74.2347, 366.3606')
Operation failed with ValueError("could not convert string to float: 'im_a_number'")
Traceback (most recent call last):
...
ValueError: math domain error
````
I think you see where this is going, try...except for each step, logging, maybe reporting specific failures
to a remote service and so on. It is already too much work for a function supposed to do a simple task.

### Solution
We will be using in this example the class ``fastchain.Chain`` (a chain constructor) 
and the utility function ``fastchain.chainable`` (similar to ``functools.partial`` with additional functionalities),


````python
from math import sqrt
from fastchain import Chain, chainable

rounded_square_roots = Chain(
    "rounded_square_roots",     # name of the chain (mandatory)
    chainable(str.split, sep=',', default_factory=list), # wrapper around str.split with a default []
    '*',    # indicates that the next function should be applied to each item of the list
    (float, sqrt, chainable(round, ndigits=2)), # sequence of 3 functions wrapped with ()
                                                # to be treated as single function with option '*'
    list    # interprets the previous generator to be a list
)
````
Let's test it:
````pycon
>>> rounded_square_roots('523.5814, 74.2347, 366.3606, 418.3412, 134.8182')
[22.88, 8.62, 19.14, 20.45, 11.61]
````
But the best part is you can plug an empty ``dict`` that will be mutated *(or filled)*
with reports, like so:

````pycon
>>> from pprint import pp
>>> reports = {}
>>> rounded_square_roots('523.5814, 74.2347, 366.3606, 418.3412, 134.8182', reports)
[22.88, 8.62, 19.14, 20.45, 11.61]
>>> pp(reports)
{'rounded_square_roots': {'rate': 1.0,
                          'expected_rate': 1.0,
                          'succeeded': 17,
                          'missed': 0,
                          'failed': 0,
                          'total': 5,
                          'failures': []}}
````
Now let's try to break it:
````pycon
>>> rounded_square_roots(None, reports)
[]
>>> pp(reports)
{'rounded_square_roots': {'rate': 0.0,
                          'expected_rate': 1.0,
                          'succeeded': 0,
                          'missed': 4,
                          'failed': 1,
                          'total': 5,
                          'failures': [{'source': 'pos[0]/str.split',
                                        'input': None,
                                        'error': TypeError("descriptor 'split' for 'str' objects doesn't apply to a 'NoneType' object"),
                                        'fatal': True}]}}
>>>
>>>
>>> rounded_square_roots('im_a_number, 74.2347, 366.3606', reports)
[8.62, 19.14]
>>> pp(reports)
{'rounded_square_roots': {'rate': 0.9333,
                          'expected_rate': 1.0,
                          'succeeded': 8,
                          'missed': 0,
                          'failed': 1,
                          'total': 5,
                          'failures': [{'source': 'pos[1]/pos[0]/float',
                                        'input': 'im_a_number',
                                        'error': ValueError("could not convert string to float: 'im_a_number'"),
                                        'fatal': True}]}}
>>>
>>>
>>> rounded_square_roots('im_a_number, -74.2347, 366.3606')
[19.14]
>>> pp(reports)
{'rounded_square_roots': {'rate': 0.8333,
                          'expected_rate': 1.0,
                          'succeeded': 6,
                          'missed': 0,
                          'failed': 2,
                          'total': 5,
                          'failures': [{'source': 'pos[1]/pos[0]/float',
                                        'input': 'im_a_number',
                                        'error': ValueError("could not convert string to float: 'im_a_number'"),
                                        'fatal': True},
                                       {'source': 'pos[1]/pos[1]/sqrt',
                                        'input': -74.2347,
                                        'error': ValueError('math domain error'),
                                        'fatal': True}]}}
````
Note that healthy branches are not impacted by other exceptions like ``[19.14]``.

And notice the failure's 'source' value, showing you the exact location of the functions that failed
with the absolute position relative to the main chain,
for further information about interpreting reports please refer to the documentation page.

### Process flow illustration
Stripping out all the handlers and decisions, the journey from ``'523.5814, 74.2347, 366.3606'``
to ``[22.88, 8.62, 19.14]`` can be visualized like the following:

<div align="center"><img src="docs/_static/diagrams/mermaid_flowchart_rounded_sqrts.svg" alt="mermaid_flowchart"/></div>

Of course, some quick decisions are made between transitions like checking the success to determine either to continue
or stop the sequence (in isolation) or even pass the given input to the next function if the failing function is not
required...

## Todo list
Next goals and ideas for upcoming versions:

 + Adding support for async functions, to support non-blocking networking and IO-bound operations.
 + Combine hybrid chain that contain async function and regular functions smoothly.
 + More IDE support and why not plugins to check chaining input output types. 

> **note**
> If you have some good ideas that need to be added please help us grow this project,
> either by suggesting or contributing in any way even by reporting issues.

# Maintainers
- [MARSO Adnan](https://github.com/mediadnan) *(author)*
