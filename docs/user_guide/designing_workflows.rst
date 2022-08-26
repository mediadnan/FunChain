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

Now before diving into details about sequences, we will first talk about how to control the process flow
using *options*;

Options
-------
We can customize a node processing behaviour or property by placing a string *(symbol)* directly before,
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

.. code-block:: python3

   >>> from fastchain import Chain
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

It's important to mention that chain iteration is **lazy** and it wasn't evaluated until ``mean``
used it, ``('*', float)`` returned a generator not a list, and we can check that

.. code-block:: python3

   >>> from fastchain import Chain
   >>> chain = Chain('test_iter', '*', float)
   >>> result = chain(['2.1', '5.3'])
   >>> type(result)
   <class 'generator'>

And if we need it to be list, we need to specify that:

.. code-block:: python3

   >>> chain = Chain('test_iter', '*', float, list)
   >>> result = chain(['2.1', '5.3'])
   >>> type(result)
   <class 'list'>

This behaviour is intentional to optimize memory usage when dealing with big chunks of data in one hand, similar to how
`map <https://docs.python.org/3/library/functions.html#map>`_, `filter <https://docs.python.org/3/library/functions.html#filter>`_
and many other builtins evaluate, and in the other hand it gives users the freedom to choose how to wrap these items
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

.. code-block:: python3

   >>> chain = Chain('my_chain', str.split, '*', float, mean)
   >>> chain(['12.5', '56.33', '54.7', '29.65'])
   my_chain/sequence[0]/str.split raised TypeError...

We can tell the chain that ``str.split`` is just an optional step like so:

.. code-block:: python3

   >>> chain = Chain('my_chain', '?', str.split, '*', float, mean)
   >>> chain(['12.5', '56.33', '54.7', '29.65'])
   38.295

It works now even when the first step fails. Before analyzing how does this work, it's
should be mentioned that the failure is still captured but not considered fatal,
and always logged but with a lower level of severity:

.. code-block:: python3

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

Which made our chain able to process both ``'12.5 56.33 54.7 29.65'`` and ``['12.5', '56.33', '54.7', '29.65'``.

Grouping nodes
--------------
TODO

Chainable
---------
TODO

Chain model
===========
TODO
