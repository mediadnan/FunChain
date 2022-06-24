
# fastchain

[![Tests](https://github.com/mediadnan/fastchain/actions/workflows/tests.yml/badge.svg)](https://github.com/mediadnan/fastchain/actions/workflows/tests.yml)
![Python versions](https://img.shields.io/pypi/pyversions/fastchain)
![PyPI version](https://img.shields.io/pypi/v/fastchain)
![License MIT](https://img.shields.io/github/license/mediadnan/fastchain)

**fastchain** *(functions' chain)* is a python3 tool aiming to ease piping functions by safely chaining
results from a function to the other sequentially or simultaneously and reporting failures without breaking the main program.

It provides tools needed for designing a process pipeline like grouping and branching, tools for creating
your own components, and tools for monitoring and debugging the chain process. All with easy and pythonic syntax. 

This system designed based on a philosophy of  **low-latency** use in favour of **cold-starts**,
in other words the chain and its components should be prepared when your program starts and be ready for use
with minimal to no configuration needed, keep it in mind when designing your chains and completely
separate configuration state *(constant process values)* that each function needs from pure input data that it expects,
that will improve the performance of your program for sure.
And for this reason it is recommended and best suited to live
in running images or any running service instead of a serverless function.

## The main benefits
- **Automation** :
    Automate any data processing pipelines just by passing your functions in the right logical order,
    then you just need to call one and the rest will be performed automatically.
- **Decoupling** :
  Lowers code dependency, so you can create components and function in different
  modules and call them in one place, no function needs to know about the other.
- **Cohesiveness** :
    Encourages you to create functions that have a single responsibility and chain them as units instead
    of chaining a function that has it internal sequence.
- **Flexibility** :
    Refactoring a sequence is a lot easier and safer, you can easily modify the structure of your process 
    flow, combine two, or reuse a part of one in the other.
- **Scalability** :
    Adding more functionality and branching is simpler, you can nest as many structures as you need and design
    complex flows faster.
- **Simplicity** :
    Providing and easy and intuitive syntax, you don't need to learn a lot to start using it
    because you get what you expect, and it's easier to visualize the process flow by just looking at the structure.
- **Typing** :
    Encourages you to use annotations *(type hinting)*, you'll get more support, warnings and debugging
    information if you use type hints, but you can still skip it...
- **Isolation** :
    Each of your functions is converted into a node that runs safely, if it fails *(raises an exception)*
    your main program will not break but only this chain will stop and report the issue.
- **Monitoring** :
    You can plug a callback function into the chain, it will be called with a report after each time this 
    chain is executed, and if any failure occurs the reporter will pinpoint the source and give you detailed information 
    about the issue reducing the debugging time and effort. You can also activate logging, so you get live log feeds after each step.
- **Performance** :
    This library has been developed with performance in mind, and it will always aim for improving it by time
    as long as there is room for better optimization.
- **Support** : 
    This is an actively maintained project, I myself rely on it in other projects and if there's any discovered
    bug it will soon be fixed, after all it's fully tested and test cases will be added regularly.
- **Standalone** :
    This project has no third party dependencies that need to be installed, it only relies on the python
    standard libraries.
- **Integrability** :
    It is easy to use it with other libraries and frameworks as it is a thin layer around your functions,
    and it supports either ways of integration, to be integrated in or to integrate other tools.

## The need
As a lazy developer among many, repetitive tasks such as validating and handling errors *(or any tedious
task)* for each step is tiring and takes away the joy and focus from the main idea of a program,
``fastchain`` was created mainly to automate chaining functions for data processing purposes
designed to live on a remote server and get notified if an anomaly occurs 
without breaking the whole system and be able to adapt quickly to change, 
reducing the refactoring energy you have to put if one of your sources changed slightly.

Read more about this tool, it might just be a solution or an improvement for one of your projects.

## Audience
This is just a utility not a complete framework, the targeted audience are developers the do any kind
of data processing with a series of functions that could fail at any step.

## Installation

You can pip-install it **fastchain** by running the command
````bash
pip install fastchain
````

## Main API

This package contains some funny names that you'll get used to, but when you read ***'chainable function'***
that means a functions that takes exactly one positional argument *(or one positional first argument and optional others)*
and returns a value, that value will be the input for the next ***chainable function*** and so on...

### *fastchain.Chain*
The main objects that you'll be using are ``Chain`` instances, 
the constructor takes the following arguments:
  + ****chainables*** are positional arguments that define the structure of your workflow, this is where
    you'll be passing your *chainable functions* and other supported types that will be shown in the examples bellow,
    passing no chainable will raise a ``ValueError``.
  + ***title*** is a required keyword argument, it must be a non-empty string, 
    and it should be unique in your program. this string is what identifies your chain in reports, logs ...
    the chain will warn you if you duplicate names.
  + ***callback*** is an optional keyword argument default to None, and it should be a function that 
    will be called back when the chain call ends, it must take the Report object as the only (positional) argument
    and return nothing. Even as it's optional it is highly recommended to pass it because this is a major 
    benefit of this package.
  + ***log*** is an optional keyword argument default to False, if set to true; the errors will be
    logged using the standard logging module.

A **chain** can be called with an input value and return the last output result.

##### Example
Let say that we want to calculate the rounded square root of a number given as a string,

````python
from math import sqrt
from fastchain import Chain

rounded_square_root = Chain(float, sqrt, round, title='rounded_square_root', callback=print)

if __name__ == '__main__':
    result = rounded_square_root("   17  ")
    assert result == 4
    assert isinstance(result, int)
````
The result will be an integer 4, this simple sequence works like this:

    "   17  " -> [float] -> 17.0 -> [sqrt] -> 4.123105625617661 -> [round] -> 4

*In fact this is overly simplified for example purposes, stripping out the decision nodes...*

The chain will also report that ```3``` operations succeeded and ```0``` failed.

In fact, we passed the builtin ``print`` function as callback,
the report will be printed to the standard output like this:
````
================================================================================
REPORT: 'rounded_square_root'
SUMMARY: all components have succeeded
    3 completed components (3 completed operations)
    0 failed components (0 failed operations)
================================================================================
````

Now if we call ``square_root`` with an invalid string like ``"a34"`` the chain will fail at the first function :

    "a34" -> [float] !! "ValueError: could not convert string to float: 'a34'" -> None

This time the chain will report ```0``` operations succeeded and ```1``` failed, the Report object will contain
all the information in case of failure such as the exception object itself (*Exception type, exception message and traceback ...*) , 
the full title of the failing component *(function)* in this case it will be ```'rounded_square_root :: float (0, 0)'```,
it follows this pattern ``[chain's name] :: [component's name] [absolute position]`` and ```(0, 0)``` means the first component
on the main sequence, the given input, the returned output, the root and the previous components.

The string aspect of the report will be as this:

````
================================================================================
REPORT: 'rounded_square_root'
SUMMARY: no component has succeeded
    0 completed components (0 completed operations)
    1 failed components (1 failed operations)
--------------------------------------------------------------------------------
FAILURES:
  rounded_square_root :: float (0, 0):
    - input: 'a34'
      output: None
      error: ValueError("could not convert string to float: 'a34'")
      root: '([float(?) -> ?] => [sqrt(?) -> ?] => [round(?) -> ?])'
      previous: 'None'
================================================================================
````

There might be other failing scenarios for example if we pass ```"-5"``` to ``square_root`` :
    
    "-5" -> [float] -> -5.0 -> [sqrt] !! "ValueError: math domain error" -> None

And that will report ```1``` operations succeeded and ```1``` failed ...

---

### *fastchain.chainable*
This is a wrapper function that lets you pass some additional metadata together with the functions,
it takes a function as a positional argument and these two optional keyword arguments:

+ **title** is optional, and it must be a non-empty ``str``, this will override the name of the decorated function. 
 if no title is passed the default will be the function's ``__qualname__``.
+ **default** is optional, it specifies the default value to be returned in case of failure, the default is ``None``.

``chainable`` can be used in two different ways, either as a function :

````python
from fastchain import chainable


def func(number: int) -> int:
    return 2 * number


new_func = chainable(func, title='double')
````

or as a decorator

````python
from fastchain import chainable


@chainable(title='double')
def func(number: int) -> int:
    return number * 2
````

And this is useful in cases like the following :

+ **Use case 1: renaming a function such as lambda functions to be more informative** : 
````python
Chain( ..., chainable(lambda x: x*2, title='double'), ..., title=... )
````
*Now if the function fails at this function the reported name will be ``'double'`` instead of ``'<lambda>'``* 

*It is bad practice to pass a raw lambda function, naming them makes it easy to identify.*
+ **Use case 2: setting the default value if the function fails** :
````python
Chain( ..., chainable(int, default=0), ..., title=... )
````
*If the function fails here the returned value will be ``0`` instead of ``None``*

*This is useful when the type or value matters regardless of the success state, and that if you're using a strict
validation system such as ``pydantic``*

*Note that you can use both ``chainable(lambda x: x*2, title='double', default=0)``* or 
none ``chainable(lambda x: x*2)``, but using none is the same as passing ``lambda x: x*2`` itself.  

---
### *fastchain.funfact*
``funfact`` stands for **function factory**, it is a decorator, and it has the same purpose as ``fastchain.chainable()``
but it decorates higher order functions *(or function factories)* and those are functions that produce functions.
this is useful when you need to prepare some settings then output a function...

You need to use this decorator in scenarios like those:

+ **Use case 1: need to prepare some state to be ready for use**

````python
from fastchain import funfact


@funfact
def my_func(*args, **kwargs):
    def func(arg: list[str]) -> str:
        pass

    # do some expensive initializations and preparations
    # based on *args and **kwargs
    return func
````
``my_func`` now takes **args* and ***kwargs* and two extra keyword arguments 
***title*** and ***default*** like ``chainable()``

Calling ``my_func`` now acts like calling ``chainable`` they both return a ``Wrapper``
object that's used by ``Chain`` to create the right component.

This
````python
@funfact
def function_factory(*args, **kwargs):
    def func(a: int) -> bool:
        pass
    # some code here
    return func

fun_config = function_factory(..., default=False)
````

Is similar to this

````python
def function_factory(*args, **kwargs):
    def func(a: int) -> bool:
        pass
    # some code here
    return func

fun_config = chainable(function_factory(...), default=False)
````

*The only difference here as we didn't specify the **title**, the first one will be ``'function_factory'``
and the second one will be ``'function_factory.<locals>.func'``*

+ **Use case 2: need to slightly modify the behaviour of the function**
````python
@funfact
def power(exponent: int):
    def func(base: float) -> float:
        return base ** exponent
    return func

main_chain = Chain(..., power(2, title='square'), ..., power(3, title='cube'))
````
+ **Use case 3: need to output a different functions for different a configurations**
````python
@funfact
def some_func(validate: bool = False):
    def func_with_validations(a: str) -> str:
        ...
    def func_optimized_no_validations(a: str) -> str:
        ...
    # some code here
    return func_with_validations if validate else func_optimized_no_validations
````
+ **Use case 4: need to use it as a class decorator**
````python
@funfact
class MyCallable:
    def __init__(self, *args, **kwargs):
        ...

    def __call__(self, arg: list[int]) -> int:
        ...
````

*If you want to use the class approach, you definitely **must** implement
the ``__call__`` dunder method, otherwise an exception will be raised.*

*And if you call MyCallable without specifying the title, the default title will be **``MyCallable instance``***

---

# Chain design options
## Map option
This option useful when you have a function that returns a list, a tuple or any iterable, and you need to apply
the next function to each item instead of applying it to all the collection at once. for this ***fastchain*** offers
an easy syntax to mark the next functions as function that need to be mapped, and that by passing ``'*'`` before them.

##### Example
Let's do some arithmetics again, consider that we have this string ``"-134.76, 103.4 , -89.34"``
and we need to extract the rounded absolute value of each number.

````python
from fastchain import Chain, funfact


@funfact
def str_split(sep: str = None):
    def split(text: str) -> list[str]:
        return text.split(sep)

    if not (isinstance(sep, str) or sep is None):
        raise ValueError('sep must be a string')
    return split


abs_rounded_values = Chain(
    str_split(',', title='split_by_commas', default=[]),
    '*',
    float,
    abs,
    round,
    title="abs_rounded_values"
)

if __name__ == '__main__':
    result = abs_rounded_values("-134.76, 103.4 , -89.34")
    assert list(result) == [135, 103, 89]
````

It works like this:

                                                                      | "-134.76" -> (float) -...-> (round) -> 135 |
    "-134.76, 103.4 , -89.34" -> (split) -> ["-134.76", ...] -> (*) ->| " 103.4 " -> (float) -...-> (round) -> 103 | -> (list) -> [135, 103, 89]
                                                                      | " -89.34" -> (float) -...-> (round) -> 89  |

*Again this is overly simplified, the ``ChainMapperOption`` produces a generator, it gets evaluated **lazily**
when we applied ``list()``. and this is an optimization detail*

*And yes, we can choose the type of collection (e.g ``list``, ``tuple``, ``set``, ...) right inside the chain,
refer to the next examples down bellow...*

##### Advantages *(Reminder)*

Basically you can achieve the same result by creating a function like this :
````python
def abs_rounded_values(text: str, sep=','):
    """gets the absolute rounded values from a string of numbers"""
    return (round(abs(float(item))) for item in text.split(sep))
````
But using a chain instead of function that do it all has better advantages :
1. It gives you **flexibility**, so you can insert, substitute or remove a step in your workflow in one place.
2. It gives you **scalability**, the chain parses its elements recursively, so you can nest and group workflows
as deep as you need, more on that down bellow.
3. It gives you **readability**, you can easily see and design the structure of your workflow.
4. It gives you **fault tolerance** and **debugging information**, and that is the most important:

Imagine that you have a backend app, and you get ```"534,abc"``` , the app will break when trying to 
convert ``'abc'`` into a ``float``, or you need to refactor your functions and add some nested ``try...except``
blocks and manually then add specific handlers for each step then attach some callback, maybe add some loggings...,
and you see that gets uglier quickly, and it's far less scalable and more error-prone...

By using the fist approach (``fastchain.Chain``), this is handled by default, in case of failures like this,
it will return a default value without breaking your code,
and calling your report callback with all the details,
the report callback can be a function that you create, it should get the report object and perform some logic on it,
like analysing it, and then dispatching some kind of event *such as sending notifications...*

---

## Grouping option
This is used for grouping a sequence of chainable functions, by default there is only one group, and it's the main 
sequence you provide to ``fastchain.Chain``, but in some cases you might need to use subgroups, and you do that by
surrounding the chainable functions by ``()``.

This is mostly needed to mark an end for a mapped sequence.

##### Example
Say that we have this raw data feed :

``"text-1, text-2, text-3"``

And we want it to be like this :

````html
<main>
    <div>text-1</div>
    <div>text-2</div>
    <div>text-3</div>
</main>
````

The code can be like that :

````python
from fastchain import Chain, funfact, chainable


@funfact
def add_tag(tag_name: str, ):
    def tag_func(text: str) -> str:
        return f"<{tag_name}>{text}</{tag_name}>"

    return tag_func


pipeline = Chain(
    (
        chainable(lambda x: x.split(','), title='split_articles'),
        '*',
        str.strip,
        add_tag('div', title='add_div_tag'),
    ),
    chainable(lambda x: ''.join(x), title='join_articles'),
    add_tag('main', title='add_main_tag'),
    title='str_to_html_pipeline'
)
````

The steps are performed like :

                                                                   | "text-1"  -> "text-1" -> "<div>text-1</div>" |                       
    "text-1, text-2, text-3" -> ["text-1", " text-2", " text-3"] ->| " text-2" -> "text-2" -> "<div>text-2</div>" | -> "<div>text-1</div><div>text-2</div><div>text-3</div> ->"<main><div>text-1</div><div>text-2</div><div>text-3</div></main>"
                                                                   | " text-3" -> "text-3" -> "<div>text-3</div>" |

Without grouping the fist part, the results wouldn't be reunited, here's two cases :
##### With grouping ``()``

                                          |-> [str.strip] -> [add_div_tag] |
    (start) -> [split_articles] -> [*] -> |-> [str.strip] -> [add_div_tag] |-> [join_articles] -> [add_main_tag] -> (end)
                                          |-> [str.strip] -> [add_div_tag] |

##### Without grouping ``()``

                                          |-> [str.strip] -> [add_div_tag] -> [join_articles] -> [add_main_tag] |
    (start) -> [split_articles] -> [*] -> |-> [str.strip] -> [add_div_tag] -> [join_articles] -> [add_main_tag] |-> (end)
                                          |-> [str.strip] -> [add_div_tag] -> [join_articles] -> [add_main_tag] |

*Grouping is also required when creating a sub-chain, the example bellow makes use of that*

*Elements between ```()``` get packed into a ``ChainGroup`` object.*

*``ChainGroup`` objects fails if **ANY** of it elements fail.*

---

## Branching option
This option is useful when you get to a step that needs to be branched, in other words multiple sub-chains depends on
the same previous result, each branch should have a unique name, the syntax for this is a ``dict``
that maps branches' names ``str`` to a chainable function, group of chainables, a dictionary or any other supported option...

You can achieve this by providing a dictionary of instructions (called Chain model) and getting back a dictionary of results.

##### Example

Let say we have a string representing a list of numbers ``"1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6"``
and we want to perform some statistics on them.

````python
from statistics import mode, mean, median
from fastchain import Chain, chainable

analyze_numbers = Chain(
    (
        chainable(lambda x: x.split(','), title='split_by_commas'),
        '*',
        int
    ),
    {
        'max': max,
        'min': min,
        'mode': mode,
        'mean': (mean, chainable(lambda dn: round(dn, 2), title='round_2d')),
        'median': median,
    },
    title='analyze_numbers'
)

if __name__ == '__main__':
    from pprint import pp

    result = analyze_numbers("1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6")
    pp(result)
````

The result will be like that:

`````
{'max': 9, 'min': 0, 'mode': 1, 'mean': 2.71, 'median': 2}
`````

If everything goes without failing, the process will be like that :

                                                         analyze_numbers / max   : (1, 2, ...) -> 9                          |
                                        | '1'  -> 1 |    analyze_numbers / min   : (1, 2, ...) -> 0                          |
    "1, 2, ..."  -> ["1", " 2", ...] -> | ' 2' -> 2 | -> analyze_numbers / mode  : (1, 2, ...) -> 1                          |-> {'max': 9, ...}
                                        |    ...    |    analyze_numbers / median: (1, 2, ...) -> 2                          |
                                                         analyze_numbers / mean  : (1, 2, ...) -> 2.7142857142857144 -> 2,71 |

If a failure occurs in the third step ``(int)``, the error will be reported under the title ``analyze_numbers :: int (0, 0, 2)``
with ``analyze_numbers`` being the title of the chain ``int`` being the name of the node and ``(0, 0, 2)`` being its
absolute position *(second 0 indicates the first subgroup and 2 indicates the third item in it)*

But if a failure occurs inside the model, say in ``round`` function, the error will be reported under the title
``analyze_numbers / mean :: round_2d (0, 1, 1)`` giving you the branch information, the component's name and the position, 
as it is the second in its main chain.

*The ``dict`` gets converted into a ``ChainModel`` object*

*``ChainModel`` objects fails if **ALL** it branches fail.*

---
## More
This is just an introduction, ``fastchain`` documentation is intended to be created later and that will cover in depth
usage and more example, it will also cover object documentation ``ChainModel``, ``ChainGroup``, ``ChainFunc``, and 
``Report`` objects.

Meanwhile, if you're an early user, those objects support ``help()`` method and can be represented with ``repr()``,
and everything is *typed* and has it own *docstring*.
After all this project is fully based on python, explore it yourself, it'll be fun.

# Upcoming features
+ Support for concurrency, to allow async functions or a mix of coroutines and normal functions and better performance for IO bound operations.
+ Serialization of chains *(json probably)*, and make it possible to modify and load predefined chains without touching the code.
+ Adding more predefined utilities, templates and shortcuts for frequent structures. 
