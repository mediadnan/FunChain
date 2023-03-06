.. _chain-models:

=========
The model
=========

FastChain simplifies how most used result structures are defined, and making the processes which are set of functions
into a single object, this is referred here as modeling.

A model is defined with multiple branch nodes, when it receives an input it passes it to it branches and returns
the results in the same defined structure.

Models currently come in two different flavors, a **dict** model and a **list** model, and as their names hint
one defines the structure of list of results *(dedicated for results that should be returned in a specific order)*,
and the other defines a structure of a dict of results *(dedicated for results that should be returned as a mapping)*.

Node models
===========
Models are define inside :ref:`make() <fastchain.make>` function by passing functions *(or other supported types)* inside
a **list** or a **dict** the same way we want our results to be, to make it clear let's use an example:

.. code-block:: python
    :emphasize-lines: 4-9

    import fastchain

    # definition
    model = {
        'number': ...,
        'type': (type, lambda t: t.__name__),
        'parity': lambda num: ('odd' if num % 2 else 'even') if isinstance(num, int) else 'none',
        'sign': lambda num: 'positive' if num > 0 else ('negative' if num < 0 else 'unsigned')
    }
    analyse_number = fastchain.make(model)

    # test
    print(analyse_number(5))    # {'number': 5, 'type': 'int', 'parity': 'odd', 'sign': 'positive'}
    print(analyse_number(-6))   # {'number': -6, 'type': 'int', 'parity': 'even', 'sign': 'negative'}
    print(analyse_number(0))    # {'number': 0, 'type': 'int', 'parity': 'even', 'sign': 'unsigned'}
    print(analyse_number(1.3))  # {'number': 1.3, 'type': 'float', 'parity': 'none', 'sign': 'positive'}

We've defined a dict-model that takes a number and gives some of its properties, the definition has the same structure
as the output where functions are replaced with results. In this case our model contains 4 branches, and its
input is passed to all those branches separately.

The first branch *number* has a **passive** node defined with Ellipsis ``...``,
a node that returns whatever was passed to it (think of it like ``lambda x: x``). For branches, it is recommended to
use ``'branch': ...`` instead ``'branch': lambda x: x`` as it's more optimized.

The second branch *type* contains a sequence of two nodes, ``type`` to extract the data-type and ``lambda t: t.__name__``
a function that accesses the name of the type. This is a good example for nested structures.

The remaining branches are functions that check some conditions to determine the kind of that number.

The first 3 branches are kinda stable but the last one is fragile, it clearly expects numbers and will fail if it receives
another type.

.. code-block:: python

    >>> analyse_number("4")
    model[sign].<lambda> raised TypeError("'>' not supported between instances of 'str' and 'int'") when receiving str: '4'
    {'number': '4', 'type': 'str', 'parity': 'none', 'sign': None}

But look what happened, the other 3 branches returned their values regardless of that failure, only the last branch
failed and returned ``None`` *(which can be replaced with another default, see later chapters)*

If we don't want that value to be included when it fails, we can make that branch optional like so:

.. code-block:: python
    :emphasize-lines: 5

    >>> analyse_number = fastchain.make({
    ...         'number': ...,
    ...         'type': (type, lambda t: t.__name__),
    ...         'parity': lambda num: ('odd' if num % 2 else 'even') if isinstance(num, int) else 'none',
    ...         'sign': ('?', lambda num: 'positive' if num > 0 else ('negative' if num < 0 else 'unsigned'))
    ... })
    >>> analyse_number(12)
    {'number': 12, 'type': 'int', 'parity': 'even', 'sign': 'positive'}
    >>> analyse_number('12')
    {'number': '12', 'type': 'str', 'parity': 'none'}

In this specific example making *sign* optional doesn't make sense, but consider this feature in other real-life processing
scenarios and the flexibility that we get with this option.

Of course the concepts are the same for a **list-model**, and here is the list version:

.. code-block:: python

    import fastchain

    def parity(num):
        if not isinstance(num, int):
            return 'none'
        elif num % 2:
            return 'odd'
        return 'even'

    def sign(num):
        if not num:
            return 'unsigned'
        elif num > 0:
            return 'positive'
        return 'negative'

    # definition
    analyse_number = fastchain.make([..., (type, lambda t: t.__name__), parity, sign])

    # test
    print(analyse_number(5))    # [5, 'int', 'odd', 'positive']
    print(analyse_number(-6))   # [-6, 'int', 'even', 'negative']
    print(analyse_number(0))    # [0, 'int', 'even', 'unsigned']
    print(analyse_number(1.3))  # [1.3, 'float', 'none', 'positive']

And now that we have a better understanding about models, let's talk about some basic rules.

.. warning::

    It is not allowed to pass an empty dict or an empty list to :ref:`make() <fastchain.make>`,
    as this will cause a `ValueError`, and a model at least requires one branch.

.. important::

    Models like all the other nodes return a value and inform the next node whether it went successful or not,
    and they will fail if any required *(none-optional)* branch fails.

