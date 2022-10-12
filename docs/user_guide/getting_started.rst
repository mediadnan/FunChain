===============
Getting started
===============
The best way of giving you an idea about this library is by showing you some use cases in a simple example,
introducing its basic API, and talking about the problems that it might solve.
However advance topics will be covered in further chapters grouped by different concepts.

Making our first chain
======================
Composing multiple functions together in a specific order to get a specific result from an input is an important concept
in mathematics, engineering and computer science just to name a few, and some purely functional programming languages
have that concept embedded in them. However, for bigger projects this may introduce problems as functions become
tightly coupled and the dependency increases and if a single function fails for a specific input the entire process
exits with an error. To address this issue, programming languages provide a way for handling exceptions,
but handling each function call can become repetitive and needs to be automated, and that what this library does.

Let's get our hands dirty and start by an example, consider that we want to calculate the average of
a sequence of numbers given as a string. more specifically `func('12.5 56.33 54.7 29.65') -> 38.295`.

This of course can be done in a single line of code ``mean(float([num for num in numbers.split()]))``,
it can pretty fast too. But in it may fail for many reasons, like if numbers were ``None`` trying to access .split()
will cause an ``AttributeError``, passing ``'1 2 X'`` will cause a ``ValueError`` inside when passed to ``float()``,
and so on, and even when logging error messages all at once, sometimes they don't give enough information about
the failure.

The FastChain way of achieving this functionality is as follows:

.. code-block:: python

    >>> from statistics import mean
    >>> from fastchain import make
    >>> chain = make(str.split, '*', float, mean)

First we imported |statistics.mean| from the standard library and :ref:`make <fastchain.make>` function from ``fastchain``
a function that creates :ref:`chain <fastchain.Chain>` objects, in this specific case the chain has 3 nodes;
``str.split()``, ``float`` and ``mean``.

The ``*`` before ``float`` indicates that the result from the previous should be iterated.

This chain is untitled, but a best practice is to always give a descriptive name for each chain as it can be very
helpful in reports. The name can be passed as a keyword argument ``name`` as follows:

.. code-block:: python

    >>> chain = make(str.split, '*', float, mean, name="number_sequence_average")

Our ``chain`` is a function-like object that has a basic api, let's explore some of its attributes:

.. code-block:: python

    >>> chain  # the chain representation
    Chain(name='number_sequence_average', required/nodes=3/3)
    >>> chain.name  # the chain name
    'number_sequence_average'
    >>> len(chain)  # chain size (str.split, float, mean)
    3

Naming chains is optional but **HIGHLY RECOMMENDED**, and helps a lot to identify them from reports when you have many chains,
it even gives the possibility of retrieving chains previously created.

.. code-block:: python

    >>> from fastchain import get
    >>> get("number_sequence_average")
    [Chain(name='number_sequence_average', required/nodes=3/3)]

Now if we want to use our chain all we have to do is call it like a normal function

.. code-block:: pycon

    >>> chain('12.5 56.33 54.7 29.65')
    38.295

Perfect, but nothing special about this and it can be achieved in a single line as previously mentioned

.. code-block:: pycon

    >>> from statistics import mean
    >>> simpler_chain = lambda numbers: mean(map(float, numbers.split()))
    >>> simpler_chain('12.5 56.33 54.7 29.65')
    38.295

Well sure, but chains are used for cases when the process might fail at any point of the code,
so let's try some few scenarios

.. code-block:: python

    >>> chain(['12.5', '56.33', '54.7', '29.65'])
    number_sequence_average.sequence[0].str.split raised TypeError("descriptor 'split' for 'str' objects doesn't apply to a 'list' object") when receiving list: ['12.5', '56.33', '54.7', '29.65']

Of course our chain doesn't expect lists, and this example shows that this exception was handled and logged
with the exact location where the failure occurred with the error and the given input,
(the name syntax will be covered on :ref:`reports chapter <reports>`),
this failure is an event that will trigger any user defined action, but the default one will be logging,
all while the app will continue running.

In addition, if we expect both string and a list of string we can make the first node (``str.split``) optional,
all we need is a slight modification:

.. code-block:: python

    >>> chain = make('?', str.split, '*', float, mean)
    >>> chain('12.5 56.33 54.7 29.65')
    38.295
    >>> chain(['12.5', '56.33', '54.7', '29.65'])
    38.295

More about options on next chapters.

We can also print execution statistics especially when testing, it shows some useful metrics about what goes on behind
scenes, this can be activated through a keyword argument:

.. code-block:: python

    >>> chain = make(str.split, '*', float, mean, print_stats=True)
    >>> result = chain(['12.5', '56.33', '54.7', '29.65'])


In addition especially when testing, you can tell the chain to print report statistics:

.. code-block:: pycon

    >>> chain = Chain('my_chain', str.split, '*', float, mean, print_stats=True)
    >>> result = chain('12.5 56.33 54.7 29.65')
    -- STATS -----------------------------
       success percentage:        100%
       successful operations:     6
       unsuccessful operations:   0
       unreached nodes:           0
       required nodes:            3
       total number of nodes:     3
    --------------------------------------

Lets try some exception

.. code-block:: pycon

    >>> result = chain('12.5 abc 54.7 29.65')
    sequence[1].float raised ValueError("could not convert string to float: 'abc'") when receiving str: 'abc'
    -- STATS -----------------------------
       success percentage:        92%
       successful operations:     5
       unsuccessful operations:   1
       unreached nodes:           0
       required nodes:            3
       total number of nodes:     3
    --------------------------------------
    >>> result
    32.28333333333333

The logging handler can be turned off when defining the chain by passing a keyword argument ``log_failures=False``,
but it is recommended to hook another report handler to the chain, because clearing all handlers will just be muting
all failures and will never be reported.

A custom handler can be attached to the chain via the ``add_report_handler`` method:

.. code-block:: python

    >>> def inform_the_staff(report: dict) -> None:
    ...     ... # some code goes here
    >>> chain.add_report_handler(inform_the_staff)

The topic of report handling will be covered in a later chapter :ref:`reports <reports>`.

Wrap-up
=======
To summarize what we've covered in this chapter, chains are object created using :ref:`fastchain.make() <fastchain.make>` where we can pass
our processing functions as positional arguments together with options, we can name the chain to identify it and register
it globally, and finally we can call it with an input that will be internally processed so the last successful result
will be returned.
The chain also has a event system for reports, so it can register one or many report handlers that will be called
at the and of each call *(or only in case of failures, depends on settings)*.

In the next chapter, we will walk through different structures of a processing pipeline that fastchain
supports.