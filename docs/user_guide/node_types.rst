==========
Node types
==========
Beside chaining functions sequentially *(which was the original purpose)*, fastchain also provides 
ways of branching a chain and iterating a collection of results.

Here we will talk about different ways of designing a chain.

Basic node
==========
An obvious but worth to be mentioned type of nodes are functions, functions are building blocks for chains, 
any functions or callable objects is wrapped by fastchain into a special callable that adds chain functionality and error handling
mechanism, the first chain function must be explicitely wrapped by ``fastchain.node()``, the next piped functions
are converted into nodes automatically by fastchain.

The ``fastchain.node()`` takes a function as argument to make a node, but also takes a group of functions as we'll later see.

To make a node, we can import it directly from ``fastchain``

.. code-block:: python

    >>> from fastchain import node
    >>> def triple(num: int) -> int:
    ...     return num*3
    >>> basic_node = node(triple)
    >>> basic_node(5)  # same as triple(arg)
    15

.. chainable_function::

It also goes without saying, that a *chainable* function must have a signature of ``(Any) -> Any``,
that means that it requires only one positional argument and returns something based on that.

Examples of *chainable* functions' signature are, ``def func(arg: Any) -> Any: ...``, ``def func(arg: Any, another='default') -> Any: ...``,
``def func(*args) -> Any: ...``, ``def func(arg: Any, *args, **kwargs) -> Any: ...``, etc...

At the end the function will be called with a exactly one argument when processing data.


The chain
=========
A chain is made by piping multiple nodes together, it is a function-like object
that takes a single argument and passes it to the first function, then passes its result as an input to the next one
until reaching the last one or stops if one of the functions fails.

To make a function, we can compose nodes using the ``|`` operator

.. code-block:: python

    >>> def double(num: int) -> int:
    ...     return num * 2
    >>> my_chain = node(triple) | triple | double
    >>> my_chain(3)  # same as double(triple(triple(3)))
    54
    >>> len(my_chain)  # counts its functions
    3


