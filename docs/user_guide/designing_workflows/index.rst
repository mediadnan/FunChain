===================
Designing workflows
===================

Introduction
============
FastChain makes it very easy when it comes to defining pipelines, with simple descriptive syntax
users can define complex workflows, which makes it very suitable to quickly implement and maintain
multiple workflows in a cleaner way.

Currently supported structures are :

**Composing functions**

.. code-block:: python

    chain = Chain('sequence', func1, func2, func3)
    chain(data)
    # works the same as
    func3(func2(func1(data)))

**Defining models**

.. code-block:: python

    chain1 = Chain('dict_model', {'name': func1, 'email': func2})
    chain1(data)
    # works the same as
    {'name': func1(data) , 'email': func2(data)}

    chain2 = Chain('list_model', [func1, func2])
    chain2(data)
    # works the same as
    [func1(data), func2(data)]

**Matching structures**

.. code-block:: python

    chain = Chain('match', match(func1, func2, func3))
    chain([data1, data2, data3])
    # works the same as
    (func1(data1), func2(data2), func3(data3))

**Looping inputs**

.. code-block:: python

    chain = Chain('iterate', '*', func)
    chain([data1, data2, data3])
    # works the same as
   [func(data1), func(data2), func(data3)]

An the best part is that we can **nest structures**

.. code-block:: python

    chain = Chain('nested',
                  {
                      "sequence": ('*', func1, func2),
                      "match": match((func3, func4), func5),
                      "model": [func5, (func6, func7)],
                  },
                  func8)

    chain([data1, data2])
    # works the same as
    func8({
      "sequence": func2((func1(data1), func1(data2))),
      "match": (func4(func3(data1), func5(data2)),
      "model": [func5([data1, data2]), func7(func6([data1, data2]))]
    })

*Structures can be nested as deep as it needed*

The chain however doesn't do anything by itself and its strongly depends on the given functions to perform,
it is responsible for coordinating between those functions and execute each one in isolation from
others all while monitoring and reporting that process.

The following chapters will cover in depth each of those chain components, but let's talk a bit about
how chains work.

The concept behind chains
=========================
When defining chains, we only describe **what** we want without describing **how** do we want it to work,
that why we call chain definitions **descriptive** and not **imperative**.
We only use hints that FastChain interprets to generate functional structures, this process
is called parsing and it's recursive, it parses nodes within nodes until reaching leaf nodes which are functions,
and that how chains support deeply nested layers.

The structures from the chain definition are converted into chain components *(called chainables)*, each
structure corresponds to a different component *(function → node, tuple → sequence, dict → mode, ...)*,
all of them share a similar interface and the chain doesn't care much about the type of *chainable*,
it just treats them equally. Actually the chain always deals with only one *chainable* which in turn deals with
its internal *chainables* and so on, ranging from a single layer to many layers.

.. TODO

.. toctree::
    :hidden:
    :maxdepth: 2

    sequence.rst
    model.rst
    match.rst
