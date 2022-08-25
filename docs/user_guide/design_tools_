================
Designing chains
================

One of the main benefits of using **FastChain** is how simple structures can be defined,
from simple python builtin objects that a chain uses to builds a series of nodes that needed to perform the desired action.

In this chapter we will walk through each of the supported structures, for simplicity, we will call them **chainables**,
and those chainables are:


**function(Any) -> Any**
   Functions *(or any callables)* that take at most only one required positional argument
   are called chainable functions, and those functions are converted to the chain's leaf nodes.
   In fact, a chain **requires** at least one chainable function to be constructed, :ref:`lean more <chain-leaf-nodes>`.

**tuple**
   Tuples of functions or any other supported chainable objects get parsed into a chain sequence,
   where each node passes its result to the next until the last one, we can optionally
   add :ref:`options <chain_options>` before each node, :ref:`lean more <chain_sequence>`.

**dict**
   Dictionaries mapping names to functions or any other supported chainables get parsed into a chain model,
   where the chain uses it as a result model, and calls each function then returns a dictionary with the same
   keys mapping to results, :ref:`lean more <chain_models>`

**list**
   Lists of functions or any other supported chainables get parsed into a chain group, a little sibling
   of the chain model, the chain calls each node and returns the results in the same order, :ref:`lean more <chain_groups>`

**special chainables**
   Other supported chainable types are pre-configured nodes made by fastchain's utility function, 
   like `chainable` or `funfact`.

.. _chain-leaf-nodes:

Leaf nodes
==========
Leaf nodes are one among other types of nodes used internally by chain objects to process data,
they are obviously the most important part of the chain and also the only nodes that actually process
the data, the rest are not more than containers of these type of nodes. In this tutorial we will simply call them nodes.

To create a one, you simply need to pass a *chainable function* to the constructor,
this function get wrapped by an object that adds some useful features to it like:

+ Identifying functions, so even if you use the same function in different chains or multiple times
  on the same chain, it will still know which one has failed and which has succeeded,
  and that's because each function will be wrapped in a new node instance and thus have a different id.

+ Give nodes a fully qualified title containing the absolute location of the node relative to the root chain and it name,
  and this is a feature used in reports to let users identify quickly the exact source of a specific failure.

+ Storing metadata option that changes its behavior, like for example ``optional`` which makes
  the function forward its input in case of failure, more on that down bellow.

+ Isolating functions with potential side effects and limiting their damage,
  so when the function raises an error it will be recorded and later reported,
  but the chain's healthy components will continue, and by extension the main program will not be impacted.
  This is due to the way nodes are implemented, inspired by the **railway pattern**.
  In other words if the execution goes with no errors the node returns the output result together 
  with a success indicator, however if an error occurs,
  it returns a failure indicator *(that informs the chain to stop executing the next components)*
  together with the default value which brings us to the next feature.

+ The possibility of storing a default value to replace the expected output value in case of failure.


.. code-block:: python3
   :name: chain_nodes_testing
   :caption: chain_nodes_testing.py
   :emphasize-lines: 11
   
   from fastchain import Chain

   def increment(a: int) -> int:
       """basically a++"""
       return a + 1
   
   def double(a: int) -> int:
       """returns twice the number"""
       return a * 2
   
   my_chain = Chain("my_chain", increment, double)
   # 'increment' and 'double' are now my_chain's nodes
   
   if __name__ == '__main__':
       assert len(my_chain)  == 2  # the chain has exactly 2 nodes
       assert my_chain(5) == 12  # the result of the input 5 is 12

In this example 12 is the result of the composition ``double(increment(5))``, my_chain calls increment and if everything goes okay
(in this case ``5 + 1 = 6``) it calls double with the result (``6 * 2 = 12``)

.. important:: 
   
   Nodes fail when an error is raised (``Exception`` *subclass instance*).


Node customization
------------------
Nodes can be customized either by :ref:`option <chain_options>` strings like all other chainable components
or using a utility function named :py:func:`chainable <fastchain>`, this function can be used
scenarios like the following:

Renaming nodes
##############
A node name is by default the function's ``__qualname__``, but sometimes it is useful to explicitly name the node
in some specific use cases like when using lambda functions to have more informative titles in case of failures. 
This is achieved with using :py:func:`chainable <fastchain>`' like so:

.. code-block:: python3

  >>> from fastchain import Chain, chainable
  >>> chain = Chain("my_chain", chainable(lambda x: x - 1, name="decrement"))
  >>> result = chain(None)
  'my_chain :: decrement' raised TypeError("unsupported operand type(s) for -: 'NoneType' and 'int'") ...
  >>> result
  None

Otherwise, if no name was given, the logging message would've been ``'my_chain :: <lambda>' raised TypeError ...``


Setting defaults
################
A default value is an exclusive attribute that only nodes have, it is the value to be returned if an failure
occurs, *after all the chain has to return something*, and by default this default value is ``None``.
But in case of a restricted return type this can be overridden, let say that the chain must return an ``int``,
we can specify that ``0`` will be the default value.

.. code-block:: python3

   >>> from fastchain import Chain, chainable
   >>> def double(a):
   ...     return a * 2
   >>> chain = Chain("my_chain", chainable(double, default=0))
   >>> result = chain(None)
   'my_chain :: double' raised TypeError("unsupported operand type(s) for *: 'NoneType' and 'int'") ...
   >>> result
   0

However in some cases it is not recommended to set mutable objects as default values, because if this value get modified in one place,
this value will be modified for the next operations too. For this, we can specify a **default_factory** instead of a **default** value.


.. code-block:: python3

   >>> from fastchain import Chain, chainable
   >>> def double_all(items):
   ...     return [item * 2 for item in items]
   >>> chain = Chain("my_chain", chainable(double_all, default_factory=list), log_failures=False)
   >>> chain(None)
   []


.. important::

   **default_factory** must be a 0-argument callable that returns a default value ``() -> 'default'``.
   like ``list`` or ``dict`` ...


.. note:: 

   If both parameters **default_factory** and **default** are passed, **default** will be ignored.


.. note:: 

   Optional nodes' default will always be the input argument that failed.

.. versionadded:: 2.0
   
   Added ``default_factory`` for when a default value needs to be a new instance for each call.


Prepare functions
#################
As previously mentioned, nodes are constructed from functions that take a single input value and return a single output value,
functions that can be chained together, one's output is another's input and so one, hints the name **chainable function**.
But in many cases we need to chain functions that takes either multiple required arguments, or have some optional argument
that somehow configure its behavior. To make a node from those functions we have two options:

Using ``lambda``
~~~~~~~~~~~~~~~~
This was the way to deal this situation in ``version 1.0``, using ``chainable`` and ``lambda`` together to make a node
with a convenient name, like so:

.. code-block:: python3

   >>> chain = Chain("my_chain", chainable(lambda n: round(n, 2), name="round_2d"))
   >>> chain(3.141592653589793)
   3.14

Using ``chainable``'s partial arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Passing additional arguments directly to ``chainable`` is a more elegant way of dealing with this kind of situations,
If the wrapper receives any positional argument or a keyword argument other than ``name``, ``default`` or ``default_factory``
it will be partially applied to the function using Python's builtin |functools.partial_docs|

.. code-block:: python3

   >>> chain = Chain("my_chain", chainable(round, ndigits=2, name="round_2d"))
   >>> chain(3.141592653589793)
   3.14

There is not magic here, this acts only as a shortcut to ``functools.partial`` and could be achieved like so:

.. code-block:: python3
   
   >>> from functools import partial
   >>> from fastchain import Chain, chainable
   >>> chain = Chain("my_chain", chainable(partial(round, ndigits=3), name="round_2d"))

.. versionadded:: 2.0

   Added partial arguments functionality.

.. _chain_options:

Options
=======
Options are simply string literals placed before a node to change it behavior,
each options has a symbol and used for a specific purpose.

Available Options are:

+-------------------------------------+-----------------------+----------------------------------------------+
|               **Name**              |      **Symbol**       |               **Placed before**              |
+-------------------------------------+-----------------------+----------------------------------------------+
|  :ref:`iterate <iterate-option>`    |  .. centered:: ``*``  | .. centered :: Any supported chainable       |
+-------------------------------------+-----------------------+----------------------------------------------+
|  :ref:`optional <optional-option>`  |   .. centered:: ``?`` | .. centered :: Any supported chainable       |
+-------------------------------------+-----------------------+----------------------------------------------+
|  :ref:`match <match-option>`        |   .. centered:: ``:`` | .. centered :: list of supported chainables  |
+-------------------------------------+-----------------------+----------------------------------------------+


.. _iterate-option:

Iterate
-------  
This option is used when we have a list of result *(or any other iterable in general)*
and we need to apply the next function to each item of this list instead of applying it to the whole list.

Let say we want to double each number of a given list,

.. code-block:: python3
   :emphasize-lines: 3

   >>> from fastchain import Chain, chainable
   >>> double = chainable(lambda x: x*2, name="double")
   >>> double_numbers = Chain("double_numbers", '*', double, list)
   >>> double_numbers([4, 2, -8, 12])
   [8, 4, -16, 24]

In this example, we passed ``*`` before ``double`` to indicate that ``double`` should be
called for each individual number of the list *(using for-loop)*, if we didn't put the ``*``
the whole list will be doubled:

.. code-block:: python3

   >>> double_numbers_wrong = Chain("double_numbers", double)
   >>> double_numbers_wrong([4, 2, -8, 12])
   [4, 2, -8, 12, 4, 2, -8, 12]


You surely noticed that we explicitly passed ``list`` at the end, that because chain iterations are applied *lazily*,
in other words ``double`` is not immediately evaluated until the next node calls it *(in this case* ``list``*)*,
``*`` only creates a generator.

This is in fact not a limitation of FastChain but an optimization feature to increase memory efficiency,
just like the builtin |builtin_filter| and |builtin_map|, this is useful when working with larger streams of data, 
and adds flexibility to choose the output type (like replacing ``list`` with ``tuple`` or ``set`` ...)

.. important:: 

   Components with *iterate-option* will immediately fail if they receive a non-iterable object,
   other type of failures will be only be reported when the iteration is evaluated.

.. note:: 

   Failing elements will be reported and completely omitted:

   .. code-block:: python3

      >>> result = double_numbers([4, 2, None, 12])
      'pos[0]/double' raised TypeError("unsupported operand type(s) for *: 'NoneType' and 'int'") after receiving None (type: <class 'NoneType'>)
      >>> result
      [8, 4, 24]

   And if all the elements fail, we still get an empty list.


.. versionchanged:: 2.0

   ``iterate-option`` is only applied to its next node-component instead of all the remaining ones.

.. _optional-option:

Optional
--------
Optional option is an indicator given to components in order to mark them as not required (*hints the name optional*),
the chain will then ignore them if they fail and only include their result in case of success,
however the failures are always recorded and reported.
In fact, marking a component as optional alters its interpretation by multiple component;

+ For a :ref:`sequence <chain_sequence>`, if an optional component fails its input will be forwarded to the next node.
+ For :ref:`models and groups <chain_models>`, an optional branch will be entirely omitted if it fails.
+ In :ref:`reports <Reports>`, the failure of an optional component is not considered **fatal** nor expected to succeed,
  and the failure will be logged with a level of ``INFO`` instead of ``ERROR``.
+ But :ref:`chain match <match-option>` makes no distinction between required and optional component, a failure is a failure.

To make a component optional, we just need to place it after ``'?'``

.. code-block:: python3
   :emphasize-lines: 4

   >>> from fastchain import Chain
   >>> def double(a):  # again
   ...     return a*2
   >>> my_chain = Chain("my_chain", '?', str.strip, double)

Now the ``my_chain`` has two nodes, one required (``double``) and another optional (``str.strip``)

If we try this

.. code-block:: python3

   >>> my_chain("    123  ")
   '123123'

The chain strips out the white-spaces and doubles the string, however if we try this

.. code-block:: python3

   >>> my_chain(2)
   4

It also works even when str.strip(2) has failed, but the failing components was optional so it can be ignored
and its input (``4``) will be forwarded to the next, we can visualized like the following:

.. image:: /_static/diagrams/node_decisions.svg

.. versionadded:: 2.0

   Introduced the concept of optional components.

.. _chain_sequence:

Chain sequence
==============
Function composition is a major feature of ``FastChain``, the fact of passing results
from one node to the next is done by chains using an internal object called **chain sequence**,
a node-like object that encapsulates a series of nodes and/or other chainable components,
when called, the sequence passes its input to the first node and returns the last node's result.

To create a sequence, you only need to pass multiple chainables or a tuple of chainables to the chain, and this
is what we've been doing previous examples like :ref:`chain_nodes_testing` when we passed ``increment`` and ``double``.

Basically, having a chain with the following structure

.. code-block:: python3

   chain = Chain(func1, func2, func3, ..., func_n)
   chain("input value")

Gives similar results as the following call *(in a prefect world)*

.. code-block:: python3
   
   func_n(...(func3(func2(func1("input value")))))

The last one is more straight forward, easy and obviously faster, but highly unsafe for programs that should continue running, 
and using chains adds some beneficial isolation and monitoring features.

Passing multiple functions to the chain's constructor ``Chain('name', func1, func2, ...)`` will be automatically
parsed into a sequence where ``func1 -> func2 -> ...`` is the main sequence, but we can explicitly use ``()``
to create **sub-sequences** that are used to group a sequence into a single component.

Applying options
----------------
Options can either be applied to each node or a whole sequence of nodes, as example,
if we need a group of nodes to iterate results given by another node we can do it like this:

.. code-block:: python3
   :caption: double_str_numbers.py

   from fastchain import Chain, chainable

   # the following chain will turn this "4, 3, 2, 8"
   # into this "8, 6, 4, 16" doubling all numbers
   
   split = chainable(str.split, sep=',', name='split_by_commas', default_factory=list)
   join = chainable(str.join, ', ', name='join_by_commas', default='')
   double = chainable(lambda x: x*2, name="double")
   
   chain = Chain('double_numbers', split, '*', (int, double, str), join)


.. code-block:: python3

   >>> from double_str_numbers import chain
   >>> chain("4, 3, 2, 8")
   '8, 6, 4, 16'

The process goes like this:

.. image:: ../_static/diagrams/iter_group_double_numbers.svg


.. important:: 

   The sequence fails if one of its *required* nodes fail.

Chain models
============
When multiple nodes expect the same input as a starting point,
the chain is expected to pass that same value to each node.
For this case, a model could be defined *(either a* ``dict`` *or a* ``list`` *of nodes)*
and the results will be returned with the same defined structure.

The fact that a same value takes multiple paths is referred by ``FastChain`` as branching,
and it comes in two different flavours:

+ ``models`` are defined with ``dict`` mapping names (``str``) to nodes, 
  useful when we need a result as a ``dict`` with similar keys mapping to nodes' results.

+ ``groups`` are defined with ``list`` of nodes, 
  useful when we need a result as a ``list`` of results with the same order of nodes.

.. _chain_models:

DictModel
-----
To create a model, we need to define de structure as we expected to be returned in a ``dict``,
the chain will replace the nodes by their results when called.

Let say we have a list of numbers and we want to perform some statistics on them,
our script will be like so:

.. code-block:: python3
   :caption: testing_model_with_stats.py
   :emphasize-lines: 6 - 12

   from statistics import mode, mean, median
   from fastchain import Chain

   chain = Chain(
      "basic_stats",
      {
         'max': max,
         'min': min,
         'mode': mode,
         'mean': (mean, round),
         'median': median,
      }
   )

   if __name__ == '__main__':
      assert chain([1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6])  == {'max': 9, 'min': 0, 'mode': 1, 'mean': 3, 'median': 2}

Note that 'mean' branch has a sequence of nodes, actually node collections
(``models``, ``sequences``, ``groups`` and ``matches``) can nest as many collections
as needed with no limits, learn more about :ref:`nesting structures <nesting_components>`.

``Models``, ``Groups`` and ``Matches`` also support *passive branches*, branches that return the given
input exactly as it is, equivalent to ``lambda x: x``. To specify a passive branch we need to pass ``...``
to the chain.

Let's modify the previous example:

.. code-block:: python3
   :caption: testing_model_with_stats.py
   :emphasize-lines: 12

   from statistics import mode, mean, median
   from fastchain import Chain

   chain = Chain(
      "basic_stats",
      {
         'max': max,
         'min': min,
         'mode': mode,
         'mean': (mean, round),
         'median': median,
         'origin': ...,
      }
   )

   if __name__ == '__main__':
      result = chain([1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6])
      print(result)  # {'max': 9, 'min': 0, 'mode': 1, 'mean': 3, 'median': 2, 'origin': [1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6]}

.. _chain_groups:

Groups
------
To create a group, we need to define de structure as we expected to be returned in a ``list``, the chain
will replace the nodes by results when called.

``Groups`` and ``Models`` share a lot of similarities, the difference between them is that a group returns
a ``list`` instead of a ``dict``.

Here's a basic usage example:

.. code-block:: python3

   >>> from fastchain import Chain
   >>>
   >>> def increment(a):
   ...     return a + 1
   >>> def double(a):
   ...     return a * 2
   >>> 
   >>> chain = Chain("testing_group", [double, increment, (double, increment, double)])
   >>>
   >>> chain(6)
   [12, 7, 26]

.. important:: 

   Models and groups will fail if a required branch fails, however if an optional branch fails,
   it will be omitted *(will not be included in results)* but it will be reported.

.. _match-option:

Matching
========
When a node receives a sequence of items and needs to apply a different function for a different item,
that can be achieved using chain matching.

To create a chain match, we need to place a ``list`` of branches after the ``:`` option to inform the chain that we want
a ``match`` not a ``group``.

Quick example, let say that we have this list of tuples ``[('one', '1'), ('two', '2'), ('three', '3'), ('four', '4')]``
and we want to uppercase the first items of each tuple and parse the second into actual integers, the code will be:

.. code-block:: python3
   :emphasize-lines: 2

   >>> from fastchain import Chain
   >>> chain = Chain('testing_match', '*', ':', [str.upper, int], list)
   >>> chain([('one', '1'), ('two', '2'), ('three', '3'), ('four', '4')])
   [['ONE', 1], ['TWO', 2], ['THREE', 3], ['FOUR', 4]]


.. important:: 

   The match is a bit more strict, it will fail for the following reasons:

   + If it receives a non-iterable object as input
   + If the input and match branches have different sizes
   + If any *(required or optional)* node fails

.. _nesting_components:

Nesting structures
==================
The best part is, any node collection (``sequence``, ``model``, ``group``, ``match`` ...) can contain another
node or collection as deep as we need it to be, no limits.
The chain parses them recursively until it reaches the elementary nodes which are functions.

So we can have structures like that

.. code-block:: python3

   Chain(
      'example',
      func1,
      func2,
      [
         (func3, '*', func4, func5),
         {
               'branch1': (func6, {'sub1': ...}),
               'branch2': ...
         }
      ],
      ...
   )



.. |functools.partial_docs| raw:: html

   <a href="https://docs.python.org/3/library/functools.html#functools.partial" target="_blank">functools.partial</a>

.. |builtin_map| raw:: html

   <a href="https://docs.python.org/3/library/functions.html#map" target="_blank">map</a>

.. |builtin_filter| raw:: html

   <a href="https://docs.python.org/3/library/functions.html#filter" target="_blank">filter</a>
