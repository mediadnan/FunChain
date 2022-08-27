===================
Designing workflows
===================
FastChain simplifies how process workflows are designed, users describe the structure with python builtin objects
then the chain parses that to internal nodes that pass results from one to another.

In this chapter we will walk through each one of those few options in details and how to define a specific workflow,
but first let's keep in mind that chains are wrappers around our functions and only add functionalities and coordinates
between them and does nothing by its own, and those functions *(callables in general)* are converted to chain nodes.

Nothing prevents us from creating chains with a single node like :code:`Chain('twice', lambda x: x*2)`
but that will only add unnecessary complications for a simple task like this,
for this reason we first need to understand where and when chains are useful, and the first use case is function chaining.

Function chaining
=================
Composing functions is necessary to perform any kind of data processing especially in functional programing paradime,
but that comes with a cost as functions could fail and composing them raises the probability of failure exponentially.
And of course like any other problem in computer science this one has several solutions like the *Monadic pattern*
and *The railway oriented programing* where functions are handled separately and the functionality is implemented once
*(DRY principle)*. ``FastChain`` shares several similarities with those existing solutions but it abstracts its mechanism
away so the users doesn't have to change their code style or refactor the code base to match the new pattern, all we
need to do is create a chain with functions in the same order our pipeline needs to be
and the rest is automatically handled.

To analyze how chains execute a sequence of functions let's come up with an abstract example;

.. code-block:: python3

   def func1(x):
       """does something..."""

   def func2(x):
       """does another thing..."""

   chain = Chain('my_chain', func1, func2)

The chain fist converts those two functions into two nodes wrapped inside a node-like object called ``Sequence``
as orchestrator that executes them, and when we call our chain with an input the execution flow
can be represented like so:

.. mermaid::

   flowchart LR
   A((start))
   F1[func1]
   F2[func2]
   D1{success?}
   D2{success?}
   N([default value])
   INP([input])
   O1([result 1])
   O2([result 2])
   Z((end))
   classDef input fill:#1b1c1c,color:#ffffff;
   A --> INP:::input
   INP --> F1
   F1 --> D1
   D1 --> |YES| O1:::input --> F2
   D1 --> |NO| N
   F2 --> D2
   D2 --> |YES| O2:::input --> Z
   D2 --> |NO| N
   N --> Z

.. note::

   Obviously a chain sequence will fail when any of its *(required)* nodes fail.

Before diving into further details, let's first talk about controlling the process flow using *options*.

Options
-------
We can customize a node processing behaviour or properties by placing a string *(symbol)* directly before,
nothing needs to be imported, and we achieve it with easy, declarative and clean syntax.

``FastChain`` currently offers the following options:

+-------------------------------------+-----------------------+----------------------------------------------+
|             **Option**              |      **Symbol**       |           **Introduced in version**          |
+-------------------------------------+-----------------------+----------------------------------------------+
|  :ref:`iteration <iterate-option>`  |  .. centered:: ``*``  |             .. centered :: 0.1.0             |
+-------------------------------------+-----------------------+----------------------------------------------+
|  :ref:`optional <optional-option>`  |  .. centered:: ``?``  |             .. centered :: 0.1.0             |
+-------------------------------------+-----------------------+----------------------------------------------+

.. _iterate-option:

Iteration
~~~~~~~~~
You might have noticed the use of ``'*'`` in an earlier example, placing it before a function indicates to the chain
that the next function will receive an iterable *(eg. list, tuple, ...)* and should be called with each member
of this iterable instead of calling it with the iterable object itself, it is the same as using a *for-loop* or
comprehension.

Let us bring back the previous example to analyze it:

.. code-block:: pycon

   >>> from fastchain import Chain
   >>> from statistics import mean
   >>> chain = Chain('my_chain', str.split, '*', float, mean)
   >>> chain('12.5 56.33 54.7 29.65')
   38.295

The body of 'my_chain' was define with this structure ``(str.split, '*', float, mean)``, here we indicate that
``float`` will receive an iterable *(namely a list of strings)* and we want to convert each of those strings to float
not the entire list, the chain processes its data like follows:

.. mermaid::

   flowchart TB
       START((start)) --> |"'12.5 56.33 54.7 29.65'"| A
       A[str.strip] --> |"['12.5', '56.33', '54.7', '29.65']"| M
       M([*]) --> |'12.5'| B1[float] -->|12.5| C
       M --> |'56.33'| B2[float] -->|56.33| C
       M --> |'54.7'| B3[float] -->|54.7| C
       M --> |'29.65'| B4[float] -->|29.65| C
       C[mean] --> |38.295| END((end))

It's important to mention that the chain iteration is **lazy** and it wasn't evaluated until ``statistics.mean``
used it, ``('*', float)`` returned a generator not a list, and we can check that

.. code-block:: pycon

   >>> from fastchain import Chain
   >>> chain = Chain('test_iter', '*', float)
   >>> result = chain(['2.1', '5.3'])
   >>> type(result)
   <class 'generator'>

And if we need it to be list, we need to specify that:

.. code-block:: pycon

   >>> chain = Chain('test_iter', '*', float, list)
   >>> result = chain(['2.1', '5.3'])
   >>> type(result)
   <class 'list'>

This behaviour is intentional to optimize memory usage when dealing with big chunks of data in one hand, similar to how |map_docs|,
|filter_docs| and many other builtins evaluate, and in the other hand it gives users the freedom to choose how to wrap these items
(``list``, ``tuple``, ``set``, ...) quickly or process it without converting it like we did with ``mean``

.. warning::

   Nodes with *iteration option* will fail immediately when receiving non-iterable objects.

.. note::

   If some or all items of the iteration fail, the failures will be reported but the process will continue
   even with an empty iterable as result. This might be a feature and flexibility for some use cases and a limitation for others,
   the truth is that this is a trade off for the previously mentioned optimization *(generator)* as it has no way
   to check for success without evaluating it.
   But this can be fixed with and middle function that checks the previous result and raises and error if not met,
   or can be implemented in the next function.

.. _optional-option:

Optional
~~~~~~~~
Nodes *(or branches)* expected to fail for some inputs and not considered required can be marked as **optional**,
and that by placing ``'?'`` before. This makes chains flexible and best suited to deal with inconsistent data,
takes as example dealing with this json *(randomly generated for this example)*

.. literalinclude:: ../examples/people-data.json
   :language: json
   :emphasize-lines: 4,5

It is clear that not all records have a birth date, and we don't want our chain
to fail when trying to access that key because we kind of expecting that.

Let comeback to the previous example and make it flexible enough to process a list of strings,
but first let's remember that it failed:

.. code-block:: pycon

   >>> chain = Chain('my_chain', str.split, '*', float, mean)
   >>> chain(['12.5', '56.33', '54.7', '29.65'])
   my_chain/sequence[0]/str.split raised TypeError...

We can tell the chain that ``str.split`` is just an optional step like so:

.. code-block:: pycon

   >>> chain = Chain('my_chain', '?', str.split, '*', float, mean)
   >>> chain(['12.5', '56.33', '54.7', '29.65'])
   38.295

It works now even when the first step fails. Before analyzing how does this work, it's
should be mentioned that the failure is still captured but not considered fatal,
and always logged but with a lower level of severity:

.. code-block:: pycon

   >>> from logging import basicConfig, INFO
   >>> basicConfig(level=INFO)
   >>> chain(['12.5', '56.33', '54.7', '29.65'])
   INFO:fastchain:my_chain/sequence[0]/str.split raised TypeError...
   38.295

And with that said, let's illustrate how the chain interpreted this failure:

.. mermaid::

   flowchart LR
       START([input]) --> A
       A["optional node"] --> D
       D{success?} --> |Yes| OUT
       D{success?} --> |No| IN
       IN([forward input]) --> B
       OUT([return result]) --> B
       B["next node"]

As this chart shows, an optional node is ignored if it fails and its input is passed to the next
node, but if it succeed the result is passed to the next node.

Which made our chain able to process both ``'12.5 56.33 54.7 29.65'`` and ``['12.5', '56.33', '54.7', '29.65']``.

Grouping nodes
--------------
It is useful in many cases to group a sequences of steps together to be treated as a block, and that what we do
always when we place a series of instructions inside a function or a loop etc... And to achieve using chains,
we simply wrap nodes with ``()``, the chain interprets that group of nodes as a single node when performing
a chain of calls and the group itself is a sub-chain that does the same in a deeper layer and so on.
We now have an idea about chain options, one may ask how can we apply an option to a sequence of nodes as a whole?
That where grouping comes in.

Consider the following scenario: We need our chain in the previous example to take a string containing numbers
and calculate the average of the **square roots** this time, both parsing floats and evaluating the square roots
are part of the same block inside a loop, and to make it happen the definition will become as follows:

.. code-block:: pycon

   >>> from fastchain import Chain
   ... from statistics import mean
   ... from math import sqrt
   >>> chain = Chain('my_chain', str.split, '*', (float, sqrt), mean)
   >>> chain('12.5 56.33 54.7 29.65')
   5.970497883795522

Note that ``(float, sqrt)`` is now a sub sequence, the main sequence contains 3 units
``str.split``, ``(float, sqrt)`` and ``mean``, the second unit itself has two units ``float`` and ``sqrt``,
hopefully this gives us a better abstract idea.
And to understand the processing step by step let's visualize it with another flowchart

.. mermaid::

   flowchart TD
       START((start))
       END((end))
       A[str.split]
       M([*])
       subgraph iteration 0
       B1[float]
       C1[sqrt]
       end
       subgraph iteration 1
       B2[float]
       C2[sqrt]
       end
       subgraph iteration 2
       B3[float]
       C3[sqrt]
       end
       subgraph iteration 3
       B4[float]
       C4[sqrt]
       end
       D[mean]

       START --> |"'12.5 56.33 54.7 29.65'"| A
       A --> |"['12.5', '56.33', '54.7', '29.65']"| M
       M --> |'12.5'| B1 --> |12.5| C1 --> |3.535...| D
       M --> |'56.33'| B2 --> |56.33| C2 --> |7.505...| D
       M --> |'54.7'| B3 --> |54.7| C3 --> |7.395...| D
       M --> |'29.65'| B4 --> |29.65| C4 --> |5.445...| D
       D --> |5.970...| END

.. warning::

   It is not allowed to pass and empty group, trying it will cause a ``ValueError``, same as
   trying to create a chain with no functions

   .. code-block:: pycon

      >>> from fastchain import Chain
      >>> Chain('empty')
      Traceback (most recent call last):
        ...
      ValueError: a sequence must contain at least one node
      >>> Chain('my_chain', str, ())
      Traceback (most recent call last):
        ...
      ValueError: a sequence must contain at least one node

.. note::

   ``()`` are not always used for sub-sequencing, but sometimes only to wrap a single function together with
   an option or multiple options for branches in particular (*explained bellow* :ref:`Chain models <chain-models>`),
   and for completeness know that ``('*', float)`` will be parsed to a single node and not a sequence.

Chainable
---------
FastChain comes with a utility to customize nodes, namey the ``fastchain.chainable`` function
that takes a function *(or any callable)* as first argument and adds metadata to create nodes with specific properties,
In this section, we'll be covering some of its use cases.

Naming nodes
~~~~~~~~~~~~
``fastchain.chainable`` can be used is to name nodes, we'll see in the next chapter (:ref:`reports`) how important names
are when it comes to failure reports. Of course as we saw earlier,
naming nodes is optional and chains take the function's ``__qualname__`` as a default node name,
but sometimes this default behaviour is not very helpful especially when working with anonymous ``lambda`` functions.

To see that in action let's create a chain that does the following:

+ evaluate the cube of a given number
+ return a templated string saying 'the cube is ...'

As far as we know those steps are slightly specific and no builtin function offers a template
'the cube is ...' for example, so either we implement a function ourselves ``def cube_string(number): ...``
or as simple as this task is, we use a ``lambda`` function.

.. code-block:: pycon

   >>> from fastchain import Chain
   >>> cube = Chain('cube-number', lambda x: x ** 3, lambda x: f"the cube is {x}")
   >>> cube(4)
   'the cube is 64'

Now watch what gets reported in case of failure

.. code-block:: pycon

   >>> cube(None)
   cube-number/sequence[0]/<lambda> raised TypeError...

The title said that a <lambda> function raised an exception and that wasn't super helpful *(although we can still identify it from the sequence index)*,
it can be confusing since we are using more than one lambda.
A better way to do this is by using ``chainable``:

.. code-block:: pycon

   >>> from fastchain import Chain, chainable
   >>> cube = Chain('cube-number',
   ...              chainable(lambda x: x ** 3, name="cube_evaluation"),
   ...              chainable(lambda x: f"the cube is {x}", name="cube_representation"))
   >>> cube(None)
   cube-number/sequence[0]/cube_evaluation raised TypeError...

No doubt that this log was more helpful than the previous, but naming nodes is not exclusively related
to lambda functions and can be used for all functions to give more specific names to a processing unit.

Defult value
~~~~~~~~~~~~
``fastchain.chainable`` can define the node's default value, a value that will be returned in case any error occurs,
by default that value is ``None``, but when the consumer of our pipeline strictly expectes a specific type we can
explicitly set a default value to whatever it needs to be and the syntax is ``chainable(<functions>, default=<default>)``

Take for example a chain expected to return a number

.. code-block:: pycon

   >>> from fastchain import Chain, chainable
   >>> chain = Chain('double', chainable(lambda x: x * 2, default=0))
   >>> result = chain(5)
   >>> result
   10
   >>> result = chain(None)
   double/<lambda> raised TypeError...
   >>> result
   0

.. note::
   
   This concept is more useful for :ref:`models <chain-models>` but now as we're dealing with sequences,
   it is important to note that when a failure occurs, the sequence returns the **last required node's default**.

   .. code-block:: python3

      Chain('testing_default', chainable(func1, default=default1), chainable(func2, default=default2))
      # in case of any failure (func1 or func2) default2 is returned

      Chain('testing_default', chainable(func1, default=default1), '?', chainable(func2, default=default2))
      # in case of any failure (func1 or func2) default1 is returned

For default values that need to be freshly generated for each call *(especially for mutable objects)*, ``fastchain.chainable``
provides an alternative keyword ``default_factory`` which takes a 0 argument function that returns a default value.

We can demonstrate it with this example:

.. code-block:: pycon

   >>> chain = Chain('split-by-commas', chainable(lambda s: s.split(','), default_factory=list))
   >>> result = chain('a,b,c,d')
   >>> result
   ['a', 'b', 'c', 'd']
   >>> result = chain(None)
   split-by-commas/<lambda> raised AttributeError...
   >>> result
   []

.. note::

   To summarize, when a failure occurs this is what happens:

   + If no default or default_factory are specified, ``None`` gets returned,
   + If default is specified, ``default`` is returned,
   + If default_factory is specified, ``default_factory()`` is returned,
   + And if both default and default_factory are specified, the default will be ignored.

Partial argument
~~~~~~~~~~~~~~~~
Functions *(callables in general)* that could be chained are functions that only take a single argument and return something,
more specifically a function that takes only one required poitional argument at most but takes a positional argument at least,
*that where the name 'chainable' got inspired*. With that in mind, functions that required more than one argument must
partially take the remaining ones before use.

Let's say that we want to round a number to two decimal places, we can do it in many ways:

.. code-block:: python3

   # define a function the use it
   def round_2d(number):
      return round(number, 2)
   Chain('round_example', round_2d)

   # use lambda function
   Chain('round_example', lambda n: round(n, 2))

   # use functools.partial
   from functools import partial
   Chain('round_example', partial(round, ndigits=2))

But the same can be done by ``chainable``

.. code-block:: python3

   Chain('round_example', chainable(round, name='round_2d', ndigits=2))

``chainable(function, *args, **kwargs)`` acts exactly like |functools.partial_docs|
when it gets positional and/or keyword arguments, actually it uses ``functools.partial`` under the hood,
and note that positional argument will be applied before the chain argument.

Let's end this section with an example:

.. code-block:: pycon

   >>> from fastchain import Chain, chainable
   >>> from statistics import mean
   >>> chain = Chain('my_chain',
   ...               chainable(str.split, sep=',', name='split-by-commas'),
   ...               '*',
   ...               float,
   ...               mean,
   ...               chainable(round, ndigits=2, name='round-2d'))
   >>> chain('12.23, 54.56, 41.88')
   36.22

.. note::

   ``chainable`` is not a replacement for ``functools.partial`` but just a superset for a cleaner code.
   if no name or default needs to be set, one can simply use the builtin ``functools.partial``.


.. _chain-models:

Chain model
===========
TODO


.. |functools.partial_docs| raw:: html

   <a href="https://docs.python.org/3/library/functools.html#functools.partial" target="_blank">functools.partial</a>

.. |filter_docs| raw:: html

   <a href="https://docs.python.org/3/library/functions.html#filter" target="_blank">filter</a>

.. |map_docs| raw:: html

   <a href="https://docs.python.org/3/library/functions.html#map" target="_blank">map</a>
