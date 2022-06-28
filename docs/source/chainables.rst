===================
Personalizing Nodes
===================

.. _chainable-usage:

Chainable
=========
This is a wrapper function that lets you pass some additional metadata together with the functions, this is mostly
needed to modify the identity and the behaviour of the function as a chain component, for more technical information
check the :ref:`chainable reference <chainable-ref>`

``chainable`` can be used in two different ways:

+--------------------------------------------+---------------------------------------------+
|   Inline                                   |                 As decorator                |
+============================================+=============================================+
|.. code-block:: python                      |.. code-block:: python                       |
|                                            |                                             |
|   from fastchain import chainable          |   from fastchain import chainable           |
|                                            |                                             |
|                                            |                                             |
|   def _func(number: int) -> int:           |   @chainable(title='double')                |
|       return 2 * number                    |   def func(number: int) -> int:             |
|                                            |       return 2 * number                     |
|   func = chainable(_func, title='double')  |                                             |
+--------------------------------------------+---------------------------------------------+

And this is useful in cases like the following

Renaming a callable to be more informative
------------------------------------------
Renaming a functions sometimes is useful especially anonymous ``lambda`` functions,
and to achieve that, you should pass the new name to :ref:`chainable <chainable-ref>`
through the keyword argument ``title``

.. code-block:: python

   Chain( ..., chainable(lambda x: x*2, title='double'), ..., title=... )

*Now if the chain fails at this step, the failure will be reported under the name* ``'double'`` *instead of* ``'<lambda>'``

.. note::
   It is bad practice to pass a raw lambda function, naming them makes it easy to identify when debugging.

Setting the default value
-------------------------
Remember that when a component fails the sequence stops at this point and returns ``None``, but sometimes
we need to override this default value, and to do that we pass the new default value to :ref:`chainable <chainable-ref>`
through the the keyword argument ``default``

.. code-block:: python

   Chain( ..., chainable(int, default=0), ..., title=... )

*Now if the chain fails at this step, the returned value will be* ``0`` *instead of* ``None``.

*This is useful when the type of the output matters regardless of the success state,
and that if you're using a validation system such as* ``pydantic`` *or the client expects a specific type in general.*

.. note::
   You can pass both **title** and **default** like ``chainable(lambda x: x*2, title='double', default=0)``

   Or none like ``chainable(lambda x: x*2)``, but passing none is the same as passing ``lambda x: x*2`` itself...


----------------------------------

.. _funfact-usage:

FunFact
=======
**FunFact** stands for *function factory*, it is also a decorator, and it has the same purpose as :ref:`chainable <chainable-usage>`
but it decorates higher order functions *(or function factories)* and those are functions that produce functions.
this is useful when you need to prepare some settings then output a chainable function based on those settings,
for more technical information check the :ref:`funfact reference <funfact-ref>`

This decorator will be useful in cases like the following

Prepare some state to be ready for use
--------------------------------------
If a function needs to be instantiated before usage, either getting data from and external resource, database or files,
or the functions simply needs some configuration to a specific use case, then using :ref:`funfact <funfact-usage>` decorator could help.

Let say that we need a component to match a specific pattern, we will create a general purpose regex matcher:

.. _regex-funfact-example:
.. code-block:: python

   import re
   from typing import AnyStr, Callable, List
   from fastchain import funfact, Chain


   @funfact
   def regex(pattern: AnyStr, flags: re.RegexFlag = re.DOTALL) -> Callable[[str], List[str]]:
       """generates a function that matches a regular expression and returns those matches"""
       def func(text: str) -> List[str]:
           matches = regex_pattern.findall(text)
           if not matches:
               # This makes sure the chain does proceed
               # if no matches where found.
               raise ValueError(f"No matches for {pattern!r}")
           return matches
       regex_pattern = re.compile(pattern, flags)
       return func

In this example, we decorated ``regex`` which is a *function factor* with ``@funfact`` decorator, now calling ``regex``
returns a ``wrapper`` [1]_ instead of ``func(text: str) -> str`` just like :ref:`chainable <chainable-usage>` does.
in fact ``regex`` now takes ``pattern`` and ``flags`` as positional arguments plus ``title`` and ``default`` keyword arguments.


Using it in chains will be like

.. code-block:: python

   chain = Chain(..., regex(r"\$\s?(\d+\.?\d*)", title="price_finder", default=()), ...)

The call to ``regex`` has produced a callable [1]_, and the regex pattern ``"\$\s?(\d+\.?\d*)"``
will only be compiled once and be available for all calls.
We'll comeback to this example in the next chapter.

.. note::
   You can use ``chainable`` for the exact same purpose, but ``@funfact`` is better suited
   to decorate higher order functions.

Comparing **@funfact** and **@chainable**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------+--------------------------------------------+
|.. centered:: Using **funfact**  |.. centered:: Using **chainable**           |
+---------------------------------+--------------------------------------------+
|.. code-block:: python           |.. code-block:: python                      |
|                                 |                                            |
|   @funfact                      |                                            |
|   def hof(*args, **kwargs):     |   def hof(*args, **kwargs):                |
|       def func(a: int) -> bool: |       def func(a: int) -> bool:            |
|           pass                  |           pass                             |
|       return func               |       return func                          |
|                                 |                                            |
|   wrap = hof(..., default=False)|   wrap = chainable(hof(...), default=False)|
+---------------------------------+--------------------------------------------+

The only difference here as we didn't specify the *title*, the first one will be named ``'hof'``
and the second one will be named ``'hof.<locals>.func'``

But as good practice, it's better to use ``funfact`` and keep ``chainable`` for simpler usage.

Produce a function based on the configuration
---------------------------------------------
Using ``@funfact`` comes handy when you need to output a function based on a specific configuration,
functions that have the same signature but have a different implementation for a specific use case.

Here's a basic example

.. code-block:: python

   @funfact
   def some_func(*args, optimize: bool = False, **kwargs) -> Callable[[str], str]:
       def func_with_validations(a: str) -> str: ...
       def func_optimized_no_validations(a: str) -> str: ...
       # some common code here ...
       return func_optimized_no_validations if optimize else func_with_validations

Now you can output either the optimized version or the other based on the value of ``optimize``.

Decorate a callable class
-------------------------

Finally, you can use ``@funfact`` as a class decorator as follows

.. code-block:: python

   @funfact
   class MyCallable:
       def __init__(self, *args, **kwargs):
           ...
       def __call__(self, arg: list[int]) -> int:
           ...

But if want to use this approach, you definitely **must** implement the ``__call__`` dunder method,
otherwise ``ValueError`` will be raised.

.. note::
   + Now calling the constructor ``MyCallable(...)`` does not return ``MyCallable`` instance,
     but a wrapper [1]_ around it.
   + If you call ``MyCallable`` without specifying the title, the default title will be ``'MyCallable'``

--------

In the next chapter, we will discuss what options do we have to design a chain ...

.. rubric:: Footnotes
.. [1] :ref:`wrappers <wrapper-ref>` are object used by :ref:`chains <chain-ref>` to create it nodes.