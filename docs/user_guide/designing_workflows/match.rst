=========
The match
=========

The match node is similar to models, it also has branches but the main difference is that this one takes a sequence
of inputs *(a list, set, tuple, ...)* and passes each of the items to a corresponding branch.

This feature is useful when we are dealing with a well known iterable structure, take for example the result
of a previous model ``[5, 'int', 'odd', 'positive']`` we know that the list contains 4 items and we know the nature
*(or meaning)* of each item. We can define a match model to have a different branch for each different item
something like ``match(func1, func2, func3, func4)``, such as ``func1`` gets applied to ``5`` and ``func2`` gets applied
to ``'int'`` and so on.

To get a better understanding let's do some examples.

Match model
===========
To define a match, we need to import :ref:`match <fastchain.match>` from ``fastchain``,
fill its branches as positional arguments, and pass it to the :ref:`make() <fastchain.make>` function.

.. code-block:: python

    >>> from fastchain import make, match
    >>> chain = make(dict.items, '*', match(str.lower, int), dict)
    >>> chain({'ONE': '1', 'TWO': '2', 'THREE': '3'})
    {'one': 1, 'two': 2, 'three': 3}

The chain contains 3 nodes in the main sequences and are; ``dict.items`` descriptor, ``match`` and dict. The match
node has the map option to loop over each pair of key-value returned by the previous node, and match itself contains
two branches are ``str.lower`` and ``int``.

The execution of ``chain({'ONE': '1', 'TWO': '2', 'THREE': '3'})`` can be visualized like the following:

.. mermaid::
    :align: center

    flowchart TD
        S((start))
        E((end))
        A[dict.items]
        M1[[match]]
        M2[[match]]
        M3[[match]]
        Mo1[[match]]
        Mo2[[match]]
        Mo3[[match]]
        B1[str.lower]
        C1[int]
        B2[str.lower]
        C2[int]
        B3[str.lower]
        C3[int]
        D[dict]

    S -->|"{'ONE': '1', 'TWO': '2', 'THREE': '3'}"| A
    A -->|"('ONE', '1')"| M1
    M1 -->|"'ONE'"| B1 -->|"'one'"| Mo1
    M1 -->|"'1'"| C1 --> |"1"| Mo1
    A -->|"('TWO', '2')"| M2
    M2 -->|"'TWO'"| B2 -->|"'two'"| Mo2
    M2 -->|"'2'"| C2 --> |"2"| Mo2
    A -->|"('THREE', '3')"| M3
    M3 -->|"'THREE'"| B3 -->|"'three'"| Mo3
    M3 -->|"'3'"| C3 --> |"3"| Mo3
    Mo1 -->|"('one', 1)"|D
    Mo2 -->|"('two', 2)"|D
    Mo3 -->|"('three', 3)"|D
    D -->|"{'one': 1, 'two': 2, 'three': 3}"|E

If this example is a bit complex, let's consider a more straightforward one:

.. code-block:: python

    def double(number):
        return number * 2

    def increment(number):
        return number + 1

    chain = make(match(double, increment))
    result = chain([5, 7])
    print(result)   # [10, 8]

The chain obviously contains one match node that contains 2 branches *double* and *increment*,
and it expects exactly an **iterable** with two items (specifically numbers).

When given ``[5, 7]`` it applies each function for the corresponding item, namely ``[double(5), increment(7)]``,
so the output result is ``[10, 8]``.

The match actually has some unique rules that need to be mentioned.

.. warning::

    It is not allowed to create a match node with less than **2 branches** as this will cause
    a `ValueError`.

.. important::

    The match will fail if it receives a none-iterable object or an iterable with a different
    size (like ``match(double, increment)`` receiving ``[5]`` or ``[5, 7, 8]``).

.. note::

    The :ref:`match <fastchain.match>` function does really create a node and we cannot
    really use an instance of it ``node = match(func1, func2, func3)``,
    as ``match(func1, func2, func3)`` only returns a node factory *(a blueprint)*
    used by :ref:`make() <fastchain.make>` to generate the match node with the specified setup.

    So we can create a reusable match-node and use it multiple times:

    .. code-block:: python

        specific_match = match(fn1, fn2, fn3)

        chain = make(func1, func2, specific_match, func3, specific_match)

    And the two generated nodes inside ``make()`` are two different objects.