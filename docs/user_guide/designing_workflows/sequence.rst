============
The Sequence
============

Chaining functions
==================
Composing functions safely was originally the main purpose of ``FastChain`` as it is an important concept
when dealing with any kind of data processing especially in functional programing, we know that
functions may fail with errors and composing them raises the failure probability exponentially
leading to undesired results forces us with two options; either put the entire pipeline within try...except
and handle any exceptions and that will cause healthy results to be ignored if a single one failed, or
handle each step of the process manually or with some function.

Of course like any other problem in computer science this one has solutions, like the *Monadic pattern*,
*The railway oriented programing* and many others patterns and tools, and ``FastChain`` shares several similarities
with existing solutions while abstracting the mechanism away so users only focus on the core concept of their programs
without the need to adapt their code to match a specific pattern.

At definition, the chain interprets a **tuple** of functions as a chain **sequence**, one of several other chain
components, it processes data through its nodes in the defined order by piping results from one to the next.

Making sequences is easy

.. code-block:: python

    chain = Chain('my_chain', func1, func2)
    # same as
    Chain('my_chain', (func1, func2))
    # but the first is more convenient

Calling chain with an input can be illustrated follows

.. mermaid::
    :align: center

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

The sequence reaches the last node if no previous *required* node fails, otherwise it stops and returns
a default value. So a sequence succeeds only when all it *required* nodes do.

And to know how node can be '*not required*', let's talk about customizing nodes using options.

Chain Options
=============
Options are *short* strings known by FastChain that modify node behaviour, each option serves
a different purpose, and FastChain currently offers the options listed bellow.

Making nodes optional
---------------------
Sometimes a node is expected to fail for some inputs, meanwhile we don't want out chain to fail for that
node's failure and simply ignore it. This can be achieved by marking the node as optional and that by
placing ``'?'`` directly before that node when defining the chain.

This feature makes the chain very flexible and best suited for dealing with inconsistent data,
to see that in action let's consider the following scenario:

    We take numbers in a string ``12.5 56.33 54.7 29.65`` and then we calculate the average ``38.295``

We can implement this with the help of a builtin function `statistics.mean <https://docs.python.org/3/library/statistics.html#statistics.mean>`_

.. code-block:: python

    >>> from functools import partial
    >>> from fastchain import Chain
    >>> from statistics import mean
    >>> chain = Chain('my_chain', str.split, partial(map, float), mean)
    >>> chain('12.5 56.33 54.7 29.65')
    38.295

As expected, the input was processed successfully. However it's not the same if we try this:

.. code-block:: python

    >>> chain(['12.5', '56.33', '54.7', '29.65'])
    my_chain/sequence[0]/str.split raised TypeError(...

The chain clearly expects a string that will be split to a list of strings,
but if we think about it, the rest of the chain can do well if ``str.split`` was an optional step,
so let's make it optional:

.. code-block:: python

    >>> chain = Chain('my_chain', '?', str.split, partial(map, float), mean)
    >>> chain(['12.5', '56.33', '54.7', '29.65'])
    38.295

Now when the first node fails, the chain goes 🤷‍♂️ *'meh , let's give it to the next'*.

The process can be visualised like the following:

.. mermaid::
    :align: center

    flowchart LR
        START([input]) --> A
        A["optional node"] --> D
        D{success?} --> |Yes| OUT
        D{success?} --> |No| IN
        IN([forward input]) --> B
        OUT([return result]) --> B
        B["next node"]

That made our chain able to process both ``'12.5 56.33 54.7 29.65'`` and ``['12.5', '56.33', '54.7', '29.65']``.

.. note::

    Note that optional failures are ignored when it comes at results, but the failure details
    are still captured and optionally reported. *(more will be covered in* :ref:`reports` *)*

Iterating input values
----------------------
In some cases, a node needs to loop over a given input instead of the input itself,
take for example a list of numbers and the node should process each number of that list instead of the list itself.
This can be done by placing ``'*'`` before that node.

In the previous example we used `functools.partial <https://docs.python.org/3/library/functools.html#functools.partial>`_
together with `map <https://docs.python.org/3/library/functions.html#map>`_ and ``float`` to achieve that

.. code-block:: python

    >>> chain = Chain('my_chain', str.split, partial(map, float), mean)

However this can be *and should be* simpler

.. code-block:: python

    >>> chain = Chain('my_chain', str.split, '*', float, mean)

Now ``(str.split, '*', float, mean)`` indicates that ``float`` will receive an iterable *(namely a list of strings)*
from ``str.split`` and we want to parse each of those strings numbers to floats.

The process can be illustrated like the following:

.. mermaid::
    :align: center

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

This behaviour is intentional, it optimizes memory usage when dealing with big chunks of data in one hand,
similar to how `map <https://docs.python.org/3/library/functions.html#map>`_,
`filter <https://docs.python.org/3/library/functions.html#filter>`_ and many other builtin functions work.
In the other hand, it gives users the freedom to choose how to wrap these items
(``list``, ``tuple``, ``set``, ...) effectively or even process theme directly
without wrapping them exactly like we did with ``mean``.

.. note::

    Nodes with the *iteration option* will of course immediately fail when receiving non-iterable objects.

.. important::

    If any item of an input causes failure, it will be reported skipped but its result will be skipped.
    And that is true even if all the items fail, the node will return an empty iterable and the chain will continue.
    This flexibility might match the expected behaviour in a range of use cases, but it might also be an unwanted
    behaviour if those results are required for the next step. The Truth is this a trade off for the previously
    mentioned optimization *(generator)* as iterating nodes has no way to check for success without being evaluated,
    which only happens at the next step.
    And if the next node really requires those items, it might raise an exception if not found, that will
    cause the chain to fail anyway.

Subsequences
============
In many cases, it is useful to group a sequences of nodes together to be treated as one single node,
at the end that what we do when we place a block of instructions inside a function or a loop etc...
And to achieve that with chains, intuitively enough we place nodes between parenthesis ``()``, that will group
them as a sub sequence. This can be useful when we want to apply an option to a sequence of nodes.

Consider the following scenario; we need our chain in the previous example to take a string containing numbers
and calculate the average of the **square roots** this time, both parsing floats and evaluating the square roots
are part of the same block inside a loop, and to make it happen the definition will become as follows:

.. code-block:: python

    >>> from fastchain import Chain
    ... from statistics import mean
    ... from math import sqrt
    >>> chain = Chain('my_chain', str.split, '*', (float, sqrt), mean)
    >>> chain('12.5 56.33 54.7 29.65')
    5.970497883795522

Note that the **main sequence** contains 3 *components*; ``str.split``, ``(float, sqrt)`` and ``mean``
while the **sub-sequence** ``(float, sqrt)`` itself contains two more *components* ``float`` and ``sqrt``,

The input is processed in two layers, let's visualize it with a flowchart

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

    Note that it's not possible to pass and empty sequence *(tuple)* when defining a chain,
    as that will cause a ``ValueError``, the same for trying to create a chain with no functions.
