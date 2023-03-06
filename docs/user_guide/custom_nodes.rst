============
Custom nodes
============

Node
=========
FastChain comes with a utility to customize nodes, namely the ``fastchain.chainable`` function
that takes a function *(or any callable)* as first argument and adds metadata to create nodes with specific properties,
In this section, we'll be covering some of its use cases.

Naming nodes
~~~~~~~~~~~~
``fastchain.chainable`` can be used is to name nodes, we'll see in the next chapter (:ref:`reports`) how important names
are when it comes to failure reports. Of course as we saw earlier,
naming nodes is optional and chains take the function's ``__qualname__`` as a default node name,
but sometimes this default behavior is not very helpful especially when working with anonymous ``lambda`` functions.

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

Default value
~~~~~~~~~~~~~
``fastchain.chainable`` can define the node's default value, a value that will be returned in case any error occurs,
by default that value is ``None``, but when the consumer of our pipeline strictly expects a specific type we can
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
more specifically a function that takes only one required positional argument at most but takes a positional argument at least,
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

``chainable`` acts exactly like |functools.partial|
when it gets positional and/or keyword arguments, actually it uses ``functools.partial`` under the hood.

Keep in mind that positional argument will be passed before the chain argument and keyword arguments after.

.. code-block:: python3

    chain = Chain('name', chainable(function, arg1, arg2, key1=arg3, key2=arg4))
    chain(arg) # calls function(arg1, arg2, arg, key1=arg3, key2=arg4)

And the following keywords (``name``, ``default``, ``default_factory``) are reserved by ``chainable`` and
will not be partially passed.

Finally let's end with a usage example:

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

    ``chainable`` is not a replacement for ``functools.partial`` but a superset for a cleaner code.
    if no name or default needs to be set, one can simply use the builtin ``functools.partial``.

