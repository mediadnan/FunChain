===============
Getting started
===============

Motivation
==========
Programing in general consists of a series of instructions that get executed one after the other, and when an instruction
fails or returns an unexpected result, that causes all the remaining instructions that depends on it to fail.

But there are many solution to that out there for that issue, some programing languages *like JavaScript, Dart, Swift ...*
have the concept of optional chaining that prevent type errors like ``obj?.attribute``, Others give
developers the responsibility to check results before passing them to the next instruction, and also we have
great design patterns to follow *(especially in functional programming paradigm)* that target this specific issue
*(like Monad and Railway oriented programming...)*. But for lazy programmers like myself, bending an entire code base
to match a specific design pattern or handle each function separately is definitively not what I want to do,
however in production we never want our application to go down if one part fails or if that fails for a specific input,
usually we make sure to wrap each part and handle it exceptions and either simply logging them or sending them
to a remote logging server, store and analyse them.

Fastchain is designed to automate and simplify this process and to give a better developer experience, by taking care
of what happens between each step *(node)* and how each failure should be handled, and simplifies the definition of
function pipelines with a declarative, intuitive and easy syntax.

In this chapter we will discover the basic use case of ``fastchain`` and make our first steps,
the next chapters will be covering specific and advanced topics in depth.


Simple pipeline
===============
Consider we want to make a function that does the following:

1. Grabs a number from a text
2. Converts it into a float
3. Calculates its square root
4. Rounds the result to two decimal places
5. Converts the result to a string

So the input will be something like ``"what is the square root of 834.89?"`` and the output will be ``'28.89'``.

The most compact way of doing this is will be something like this:

.. code-block:: python

    >>> import re, math
    >>> NUMBERS_RE = re.compile(r'-?(\d+(\.\d*)?|\.\d+)')    # regex pattern that matches integer or decimal numbers
    >>> find_square_root = lambda text: str(round(math.sqrt(float(NUMBERS_RE.search(text).group())), 2))
    >>> find_square_root("what is the square root of 834.89?")
    '28.89'

An alternative and more readable way of creating this function will be like:

.. code-block:: python

    >>> import re, math
    >>> NUMBERS_RE = re.compile(r'[+-]?(\d+(\.\d*)?|\.\d+)')
    >>> def find_square_root(text: str) -> str:
    ...     number_match = NUMBERS_RE.search(text)  # step 1: grab a number from text
    ...     number = float(number_match.group())    # step 2: converts it into a float
    ...     number_sqrt = math.sqrt(number)         # step 3: evaluate the square root
    ...     rounded_sqrt = round(number_sqrt, 2)    # step 4: round to two decimal places
    ...     return str(rounded_sqrt)                # step 5: convert to string again
    >>> find_square_root("what is the square root of 834.89?")
    '28.89'

This works fine and fast, however steps 1, 2 and 3 are potential points of failure, so check this out:

.. code-block:: python

    >>> find_square_root(834.89)    # step 1: fails because re.Pattern.search expects a str/bytes
    Traceback (most recent call last):
        ...
    TypeError: expected string or bytes-like object, got 'int'
    >>> find_square_root("what is the square root of ABC?")   # step 2: fails because there's no number match
    Traceback (most recent call last):
        ...
    AttributeError: 'NoneType' object has no attribute 'group'
    >>> find_square_root("what is the square root of -16?")  # step 2: fails because math.sqrt expects a positive number
    Traceback (most recent call last):
        ...
    ValueError: math domain error

A simple fix to that problem will be wrapping ``find_square_root`` call inside ``try/except`` block

.. code-block:: python

    >>> import logging
    >>> try:
    ...     find_square_root(834.89)
    ... except Exception as error:
    ...     logging.error(error)
    ERROR:root:expected string or bytes-like object, got 'float'
    >>> try:
    ...     find_square_root("what is the square root of ABC?")
    ... except Exception as error:
    ...     logging.error(error)
    ERROR:root:'NoneType' object has no attribute 'group'
    >>> try:
    ...     find_square_root("what is the square root of -16?")
    ... except Exception as error:
    ...     logging.error(error)
    ERROR:root:math domain error

This prevents the propagation of failure, but in one hand it gets repetitive and in the other hand the message is
a bit too broad and doesn't pinpoint the failure source.

We can make it even better by rewriting the function like so:

.. code-block:: python

    >>> import re, math, logging
    >>> NUMBERS_RE = re.compile(r'[+-]?(\d+(\.\d*)?|\.\d+)')
    >>> logging.basicConfig(level=0, format='[{levelname}] {name}: {message}', style='{')  # config logging template
    >>> def find_square_root(text: str) -> str | None:
    ...     logger = logging.getLogger(f'{__name__}.{find_square_root.__name__}')  # get logger for this function
    ...     try:
    ...         number_match = NUMBERS_RE.search(text)
    ...     except TypeError as error:
    ...         logger.getChild('matching').error(error)    # pinpointing the step that caused failure
    ...         return                                      # return None, no need to continue
    ...     try:
    ...         number = float(number_match.group())
    ...     except AttributeError as error:
    ...         logger.getChild('casting').error(error)
    ...         return
    ...     try:
    ...         number_sqrt = math.sqrt(number)
    ...     except ValueError as error:
    ...         logger.getChild('square_root').error(error)
    ...         return
    ...     rounded_sqrt = round(number_sqrt, 2)
    ...     return str(rounded_sqrt)

Now that our function is ready, let's test it:

.. code-block:: python

    >>> result = find_square_root("what is the square root of 834.89?")
    >>> result  # str
    '28.89'
    >>> result = find_square_root(834.89)
    [ERROR] __main__.find_square_root.matching: expected string or bytes-like object, got 'float'
    >>> result  # None

    >>> result = find_square_root("what is the square root of ABC?")
    [ERROR] __main__.find_square_root.casting: 'NoneType' object has no attribute 'group'
    >>> result  # None

    >>> result = find_square_root("what is the square root of -16?")
    [ERROR] __main__.find_square_root.square_root: math domain error
    >>> result  # None

Perfect, it works as we expected, wrapping the failure and logging it.

But look how we started with a single line lambda function and ended up with more than 20 lines of code, it's just
too much for a function that only "evaluates a square root from a string", and this approach has multiple disadvantages:

**Unscalable**
    It gets difficult if we want to add functionality to the function or reuse the same approach
    *(wrap in* ``try/except`` *block and log)* in other functions.

**Inflexible**
    If we want to change the error handling logic, we will have to change it in each of the function definitions.

**Error-prone**
    It's easy to miss a possible exception in one of the steps or miss a probable source of failure.

**Tedious**
    The same code is repeated multiple times and this is an anti-pattern, bad practice and tiring process.

Of course any decent developer will create functions that automates these steps and handles failures,
but even that is additional work... ``fastchain`` handle that for you out of the box.


Using fastchain
---------------
Now we will implement the same function ``find_square_root`` using ``fastchain``'s tools.

.. note::

    Make sure to :ref:`install <installation>` ``fastchain`` first to be able to use it.


.. literalinclude:: examples/getting_started_fastchain_example.py
    :language: python
    :caption: fastchain_test.py

That's it, we just declare the functions to be called sequentially and fastchain
will make a chain from that.

.. important:: 

    It is necessary to wrap the first function within ``fastchain.node()``,
    a utility that converts a function into a *"chainable"* node.

.. note:: 

    We could also wrap each function inside ``fastchain.node()``, but fastchain
    does that automatically and it is useless to do it manually unless we want to
    customize a specific node.

Now let's see what we got

.. code-block:: python

    >>> from fastchain_test import find_square_root
    >>> find_square_root
    fastchain.Chain('find_square_root', len=6)

It already got the name from the variable's name and the count of nodes *(steps)*.
now let check it functionality.

.. code-block:: python

    >>> result = find_square_root("what is the square root of 834.89?")
    >>> result
    '28.89'
    >>> result = find_square_root(834.89)
    [ERROR] find_square_root.re_Pattern_search: expected string or bytes-like object, got 'float'
    >>> result  # None

    >>> result = find_square_root("what is the square root of ABC?")
    [ERROR] find_square_root.re_Match_group: 'NoneType' object has no attribute 'group'
    >>> result  # None

    >>> result = find_square_root("what is the square root of -16?")
    [ERROR] find_square_root.math_sqrt: math domain error
    >>> result  # None


And as expected all nodes are executed in isolation from the rest
and failures are well reported out of the box. Of course as we will later see,
the failure handling behaviour is fully customizable, but the default logging
handler is already not bad.
