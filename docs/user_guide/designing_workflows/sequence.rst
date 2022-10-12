============
The Sequence
============

Composing functions sequentially was the original intention of this library, as it solves the problem of performing
a series of calls to multiple functions that could fail at any step or for some specific inputs when processing data.
Of course like any other problem in computer science this one has multiple solutions depending on the use case,
ranging from design patterns like the *Monadic pattern* and *The railway oriented programing* and third party libraries
like one. ``FastChain`` shares several similarities with those existing solutions while abstracting the mechanism away
so users only focus on the core concept of their programs without the need to adapt their code to match a specific pattern.
But it should be mentioned that the ``FastChain`` library is especially inspired by the *railway pattern*,
where results from a function can take a successful or an unsuccessful track.

Node sequence
=============
As mentioned in the previous chapter, a **sequence** is defined by a **tuple** of functions or other supported types,
but usually the main sequence is defined by passing positional arguments to the :ref:`make() <fastchain.make>` function.

The syntax is like:

.. code-block:: python

    from fastchain import make

    sequence_chain = make(func1, func2)

    # same as
    sequence_chain = make((func1, func2))
    # but the first is more convenient and simple

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

Node Options
============
Options are strings known by FastChain that modify node behaviour, each option serves
a different purpose, the currently available options are the following.

Map option
----------
One useful option is to call a function for each value of an input, say that one function returns
a list but we want to apply the next function for items of that list and not the list itself,
for that purpose **map option** is used by placing a ``'*'`` before the node that needs to loop.

If we comeback to a previous example, we can see the map option being used:

.. code-block:: python

    from statistics import mean
    from fastchain import make

    chain = make(str.split, '*', float, mean)

The alternative code *(stripping away the exception handling context)* will be like this

.. code-block:: python

    from statistics import mean

    chain = lambda numbers: mean(map(float, numbers.split()))

Or in a clearer syntax like:

.. code-block:: python

    from statistics import mean

    def chain(numbers: str) -> float:
        number_list = []
        for str_number in numbers.split():
            number = float(str_number)
            number_list.append(number)
        average = mean(number_list)
        return average

The ``(str.split, '*', float, mean)`` setup creates a chain when called with an input,
the process flow can be visualized as follows:

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

It's important to mention that nodes with a **map option** are **lazily** evaluated, and the iteration and processing
happens until the next function is called.

The ``('*', float)`` part was only evaluated when called inside ``statistics.mean``, as it only returns a **generator**.

.. code-block:: python

    >>> from fastchain import make
    >>> chain = make('*', float)
    >>> result = chain(['2.1', '5.3'])
    >>> type(result)
    <class 'generator'>

And if we need it to be list, we need to explicitly specify that:

.. code-block:: pycon

    >>> chain = make('*', float, list)
    >>> result = chain(['2.1', '5.3'])
    >>> type(result)
    <class 'list'>

This behaviour was intentional to optimize memory usage when dealing with big chunks of data in one hand,
similar to how `map <https://docs.python.org/3/library/functions.html#map>`_,
`filter <https://docs.python.org/3/library/functions.html#filter>`_ and many other builtin functions work,
and in the other hand, it gives users the freedom to choose how to wrap these items
(``list``, ``tuple``, ``set``, ...) efficiently or even process them directly
without keeping them in memory exactly like we did with ``mean``.

.. warning::

    Nodes with the **map option** will fail when receiving non-iterable objects *(obviously)*.

.. important::

    If an item from an iterable input fails, it will be **reported** and its result will not be included in results,
    however the pipeline will continue even if all items fails individually and the iterating node returns an empty generator.
    This flexibility might match the expected behaviour in a range of use cases, but it might also be an unwanted
    behaviour if those results are required for the next step. The Truth is this a trade off for the previously
    mentioned optimization *(lazy evaluation)* as nodes with map option has no way to check for success,
    which only happens at the next step.
    The solution is to implement some kind of checks in the next function.

Optional option
---------------
When a node is expected to fail for some inputs, meanwhile we don't want out chain to fail for that
specific failure and simply ignore it. This can be achieved by marking the node as optional and that by
placing ``'?'`` directly before that node when defining the chain.

This feature makes the chain very flexible and best suited for dealing with inconsistent data,
so let's comeback to our example where a chain was defined with the following setup ``(str.split, '*', float, mean)``

Trying anything other than a string will cause a failure in the first node, for example passing
a list of string numbers numbers

.. code-block:: python

    >>> chain(['12.5', '56.33', '54.7', '29.65'])
    sequence[0]/str.split raised TypeError(...

This was expected as the str.split() descriptor expects a string and not a list,
but if we think about it a little, the rest of the pipline is kinda independent in that case and
can do well if ``str.split`` was an optional step, so let's make it optional:

.. code-block:: python

    >>> chain = make('?', str.split, '*', float, mean)
    >>> chain(['12.5', '56.33', '54.7', '29.65'])
    38.295

Now when the first node fails, the chain goes 🤷‍♂️ *'meh , let's give that input to the next one'*.

The process flow is visualised like the following:

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

    >>> from statistics import mean
    ... from math import sqrt
    ... from fastchain import make
    >>> chain = make(str.split, '*', (float, sqrt), mean)
    >>> chain('12.5 56.33 54.7 29.65')
    5.970497883795522

Note that the **main sequence** contains 3 nodes; ``str.split``, ``(float, sqrt)`` and ``mean``
while the **sub-sequence** ``(float, sqrt)`` itself contains two more nodes ``float`` and ``sqrt``,

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

    Note that it's not allowed to pass an empty tuple when defining a chain,
    as that will cause a ``ValueError``, the same will happen when trying to create a chain with no functions.
