===================
Designing workflows
===================
FastChain makes it easy when it comes to defining chains, with some simple **descriptive** way
we can define relatively complex workflows, we only describe **what** we expect in our processing flow
without much worrying about **how** we want it to work, which makes this it very suitable for quickly making
and maintaining multiple workflows in a cleaner way.

The process of taking user descriptive hints and converting it into actual functioning components is done
by fastchain recursively to support nested processing layers, each specific object is converted into its corresponding
component *(or node)* and the leaf nodes are functions.
In this introduction chapter we won't go deeper into details,
and we will only cover the abstract syntax of some structures that :ref:`fastchain.make() <fastchain.make>` function supports
and how they get interpreted and converted into actual hierarchical node structure.

For the abstract examples, consider that we have multiple functions defined as:

.. code-block:: python

    def func1(arg):
        ... # some code here

    def func2(arg):
        ... # some code here

    def func3(arg):
        ... # some code here

    ... # some other functions

And let's talk about different ways of creating chains.

Node sequences
==============
The main and most obvious structure that :ref:`make() <fastchain.make>` supports is the sequential function composition,
such as one function passes its result to the next and so on until the last one is reached.
The details and rules will be covered in later chapters, but the definition syntax is like follows:

.. code-block:: python

    # definition
    chain = make(func1, func2, func3)
    # usage
    chain(data)

This works similar to:

.. code-block:: python

    func3(func2(func1(data)))

In general, a **tuple** of callables *(or any other supported structure)*
is converted into a sequence, so the definition can also be done like this:

.. code-block:: python

    chain = make((func1, func2, func3))

Or

.. code-block:: python

    sequence = (func1, func2, func3)
    chain = make(sequence)

Node models
===========
Another useful feature is defining a result collection either a dictionary or list
with a specific structure and values that depend of the same input, this is referred to as models.

As mentioned, there is two types of models, dict-models for named branches and list-models for ordered branches.

The dict-model can be defined as follows

.. code-block:: python

    # definition
    chain = make({'name': func1, 'email': func2})
    # usage
    chain(data)

This works similar to:

.. code-block:: python

    {'name': func1(data) , 'email': func2(data)}

And list-models can be defined as follows

.. code-block:: python

    # definition
    chain = make([func1, func2])
    # usage
    chain(data)

This works similar to:

.. code-block:: python

    [func1(data), func2(data)]

In general, a **dict** or **list** of callables *(or any other supported structure)*
is converted into a model, so the definition can also be done like this:

.. code-block:: python

    model = {'key1': func1, 'key2': func2}
    # or model = [func1, func2]
    chain = make(model)

Unlike node sequences that compose functions sequentially,
models kind of composes them in parallel *(usually referred to as branches instead of steps)*

Node matches
============
The models are good if we want to define the result structure that depends from a single input, however if our
branches depend on different inputs, we can match each input to a corresponding branch using :ref:`fastchain.match() <fastchain.match>`

.. code-block:: python

    from fastchain import make, match
    # definition
    chain = make(match(func1, func2, func3))
    # usage
    chain([data1, data2, data3])

This works similar to:

.. code-block:: python

    (func1(data1), func2(data2), func3(data3))

Again, this can be separated like so:

.. code-block:: python

    branches = match(func1, func2, func3)
    chain = make(branches)

.. note::

    The :ref:`match() <fastchain.match>` utility must be used in this case to indicate input matching structure instead
    of a normal sequence.

Options
=======
Another supported hints are *options*, a few characters that controls the behaviour of nodes.

Options will be covered in later chapters, but one main option is the looping/iterating option hinted by ``'*'``,
and it is used like so:

.. code-block:: python

    # definition
    chain = make('*', func1, func2)
    # usage
    chain([data1, data2, data3])

This causes func1 to be called with each value of the list instead of being called with the entire list, it works
similar to:

.. code-block:: python

    func2((func1(output) for output in [data1, data2, data3]))

Nesting nodes
=============
The best part is that structures are parsed recursively, so a sequence can contain another sequences or models, and
models can contain other sequences or models and so on, that will result in a tree like structure making fastchain
very flexible when it comes at designing workflows.

This chain structure:

.. code-block:: python

    # definition
    chain = make({
                      "sequence": ('*', func1, func2),
                      "match": match((func3, func4), func5),
                      "model": [func5, (func6, func7)],
                  },
                  func8)
    # usage
    chain([data1, data2])

Works similar to this:

.. code-block:: python

    func8({
      "sequence": func2((func1(data1), func1(data2))),
      "match": (func4(func3(data1), func5(data2)),
      "model": [func5([data1, data2]), func7(func6([data1, data2]))]
    })

And nodes can be nested as deep as it needed...

In the following chapter we will dive deeper into sequences, check it out 👉

.. toctree::
    :hidden:
    :maxdepth: 2

    sequence.rst
    model.rst
    match.rst
