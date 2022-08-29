.. _reports:

=======
Reports
=======
This chapter will cover chain reports that get generated after each call and hold useful information about
the processing including failures if there's any. This feature makes it easy to monitor the chain processes
and identify the cause and the location of each failure to quickly fix it.
And makes it easy to introduce another to capture reports or even multiple handlers.

Default handler
===============
By default chains come with a **report handler**, the one that logs failures.
It uses the standard |logging.Logger_docs| to report failures with a level ``logging.ERROR`` for fatal failures
*(from required components)* and ``logging.INFO`` for expected ones *(from optional components)*.

.. code-block:: pycon

    >>> from fastchain import Chain
    >>> from logging import basicConfig
    >>> basicConfig(level=20)
    >>> def decrement(arg: int) -> int:
    ...     if not arg:
    ...          raise ValueError("the number can no longer be decremented")
    ...     return arg - 1
    >>> chain = Chain('test', decrement, '?', decrement)
    >>> chain(0)
    ERROR:fastchain:test/sequence[0]/decrement raised ValueError('the number can no longer be decremented') when receiving <class 'int'>: 0
    >>> chain(1)
    INFO:fastchain:test/sequence[1]/decrement raised ValueError('the number can no longer be decremented') when receiving <class 'int'>: 0
    0

Note that the default logger comes with the name **"fastchain"**, however this can be set to any other name by passing it as a keyword argument
``logger``

.. code-block:: pycon

    >>> chain = Chain('test', decrement, logger='my_logger')
    >>> chain(0)
    ERROR:my_logger:test/decrement raised ValueError('the number can no longer be decremented') when receiving <class 'int'>: 0

The chain uses that name and calls ``logging.getLogger(<the name>)`` to get the logger, but we can also pass an actual instance of ``logging.Logger``
with ``logger`` keyword if we need more control about the logger too.

.. code-block:: pycon

    >>> from logging import Logger
    >>> from fastchain import Chain
    >>> logger = Logger('my_logger')
    >>> ...
    >>> logger.addHandler(handler)
    >>> chain = Chain('test', decrement, logger=logger)

We can also print statistics by adding a setting the keyword ``print_stats=True``

.. code-block:: pycon

    >>> chain = Chain('test', decrement, decrement, decrement, print_stats=True)
    >>> chain(0)
    -- STATS -----------------------------
       success percentage:        0%
       successful operations:     0
       unsuccessful operations:   1
       unreached nodes:           2
       required nodes:            3
       total number of nodes:     3
    --------------------------------------
    ERROR:fastchain:test/sequence[0]/decrement raised ValueError('the number can no longer be decremented') when receiving <class 'int'>: 0
    >>>chain(2)
    -- STATS -----------------------------
       success percentage:        67%
       successful operations:     2
       unsuccessful operations:   1
       unreached nodes:           0
       required nodes:            3
       total number of nodes:     3
    --------------------------------------
    ERROR:fastchain:test/sequence[2]/decrement raised ValueError('the number can no longer be decremented') when receiving <class 'int'>: 0

And of course, we can disable this handler by setting ``log_failures=False``.

.. code-block:: pycon

    >>> chain = Chain('test', log_failures=False)
    >>> chain(0)
   
.. warning::

    Disabling the default logger should be done only if it will be substituted with another
    user custom handler *(as shown in the next section)*, otherwise errors will be muted and ignored.

    Ignoring errors is not a desired behaviour in production, but it might be useful
    for benchmarking, as reports get generated only when a handler is present but chain components
    will always be reporting stat.

.. note::

    When setting ``log_failures=False``, ``print_stats=True`` will have no effect.

Setting a report handler
========================
The default logging handler can be enough for simple use cases, but it's not always the desired action to report failures
when working with bigger projects and logs are not enough. For that, chains can register custom report handlers defined
by the user, a function that takes a dict *(report)* and expected to return nothing.

To see that in action, we will be passing ``pprint.pprint()`` as report handler and disable the default.

.. code-block:: pycon

    >>> ... # with decrement already defined
    >>> from pprint import pprint
    >>> chain = Chain('test', decrement, '?', decrement, log_failures=False)
    >>> chain.add_report_handler(pprint)
    >>> chain(0)
    {'failed': 1,
     'failures': [{'error': ValueError('the number can no longer be decremented'),
                   'fatal': True,
                   'input': 0,
                   'source': 'test/sequence[0]/decrement'}],
     'missed': 1,
     'rate': 0.0,
     'required': 1,
     'succeeded': 0,
     'total': 2}
    >>> chain(1)
    0

In the above example we added the pretty printer as handler, it get called for ``chain(0)`` as it failed
but not for ``chain(1)`` even when the second step failed, and that is because the second node was marked
as optional and so the chain ignored it when it failed and returned the last successful value.
But we can also let the chain call our handler even when the process is successful.

.. code-block:: pycon

    >>> chain.add_report_handler(pprint, always=True)
    >>> result = chain(1)
    {'failed': 1,
     'failures': [{'error': ValueError('the number can no longer be decremented'),
                   'fatal': False,
                   'input': 0,
                   'source': 'test/sequence[1]/decrement'}],
     'missed': 0,
     'rate': 0.5,
     'required': 1,
     'succeeded': 1,
     'total': 2}
    >>> result
    0
    >>> result = chain(3)
    {'failed': 0,
     'failures': [],
     'missed': 0,
     'rate': 1.0,
     'required': 1,
     'succeeded': 2,
     'total': 2}
    >>> result
    1

And of course, it is possible to add multiple handlers if that's needed

.. code-block:: python3

    # some code here ...
    chain.add_report_handler(handler1)
    chain.add_report_handler(handler2, True)
    # some code here ...

This might be useful if some chains have common report handling and others need additional handling,
those handlers are called in the same order they've been registered.

.. warning::

   Keep in mind that the same report (**mutable** dict) is shared between all the handlers, and if it
   gets modified by one handler *(which shouldn't happen unless it's intentional)* it will be modified
   for all the next handlers. And make sure your handler doesn't make the chain slow,
   :ref:`learn more <optimization_beware_of_report_handling>`.

Reports
=======
A report is a dictionary that the chain generates after each call, it contains minimal yet useful processing info
and a list of failures that happened during the processing. It is how chains communicate processing errors
as the all get captured and let us monitor their behaviour.

Reports are rigid, and their content can be illustrated with the following schema:

.. code-block:: python3

    {
        "rate": float
        "succeeded": int
        "failed": int
        "missed": int
        "required": int
        "total": int
        "failures": [
            {
                "source": str
                "input": Any
                "error": Exception
                "fatal": bool
            },
            ...
        ]
    }

In this section we will go through each of these metrics to better understand reports.

Rate
----
When the chain performs a series of processing steps through it nodes, it knows which ones have succeeded and
which have failed then calculates the success rate, a ratio of successful nodes over total number of nodes.
So ``1.0`` means everything has succeeded and ``0.0`` means everything has failed, anything in between
implies a mixture of both. So how does the node succeeds?

Nodes *(functions)* fail when an exception is raised while processing, but sometimes the same node is called
in a loop and it succeeds in some operations and fail in others, take this example:

.. code-block:: pycon

    >>> from fastchain import Chain
    >>> chain = Chain('parse_ints', '*', int, list, log_failures=False)
    >>> chain.add_report_handler(print, True)
    >>> chain(['12', '64', '38', '6M'])
    {'rate': 0.875, 'succeeded': 4, ...

For that case the node's partial success ratio is calculated by dividing the successful operations over the total number
of operations for that node. We can get the previous result using this formula:

.. math::

   \begin{equation}
   rate = \frac{3/4 + 1}{2} = 0.875
   \end{equation}

Where **3** is the number of successful operations of ``int`` over **4** its total executed operations
and **1** is 1/1 successful operation of ``list`` all over **2** which is the number of nodes (``int``, ``list``).

.. note::

    Multiplying the success rate by 100 gives us the success percentage:
    :math:`0.875 \times 100 = 87.5 \%`

Succeeded
---------
The number of operations reported successful, it might exceed the total number of nodes
when applying the ``*`` option because the same node get called multiple time thus it might succeed many times.

The chain has no way of knowing how much time the same node could be called until it get called, as this fully depends
on the size of the processed data that will be iterated.

Failed
------
The number of operations reported unsuccessful due to an exception being raised, this includes both failures
from required and optional nodes and a good indicator of how many error happened during the execution.

Like *Succeeded*, *Failed* might also exceed the total number of nodes when applying the ``*`` option.

Missed
------
The number of missed nodes, as the chain knows its nodes, some of them might be unreached due to a failure
in a previous required node that cause the process to end before reaching it.

.. code-block:: pycon
    :emphasize-lines: 8

    >>> from fastchain import Chain
    >>> chain = Chain('test_chain', str.split, len, print_stats=True)
    >>> chain(None)
    -- STATS -----------------------------
       success percentage:        0%
       successful operations:     0
       unsuccessful operations:   1
       unreached nodes:           1
       required nodes:            2
       total number of nodes:     2
    --------------------------------------
    test_chain/sequence[0]/str.split raised TypeError...

Here the failure occurred when trying ``str.split(None)`` and the ``len`` was never called because
the chain failed earlier.

Required
--------
The number of required *(non-optional)* nodes, by default, if not node or collection of nodes is marked
as optional *(with ``?`` option)* all nodes are required. However, this metric is useful when we have a bigger
structure with a mix of required and optional branches and nodes.

This example shows the report of two successful chain calls:

.. code-block:: pycon
    :emphasize-lines: 6, 7, 9, 16, 17, 19

    >>> from fastchain import Chain
    >>> chain = Chain('test_chain', lambda x: x*2, '?', round, print_stats=True)
    >>> chain(2)
    -- STATS -----------------------------
       success percentage:        100%
       successful operations:     2
       unsuccessful operations:   0
       unreached nodes:           0
       required nodes:            1
       total number of nodes:     2
    --------------------------------------
    4
    >>> chain('2')
    -- STATS -----------------------------
       success percentage:        50%
       successful operations:     1
       unsuccessful operations:   1
       unreached nodes:           0
       required nodes:            1
       total number of nodes:     2
    --------------------------------------
    '22'

Total
-----
Intuitively, the total number of nodes the chain has, or in other words how many functions *(callables in general)*
the chain was defined with, and even when the same function is passed to the definition multiple times,
each time it will be considered a new node as it logically has different roles in different pipeline positions.

.. note::

    The ``total`` number of nodes like ``required``, are evaluated early when the chain is defined and not until
    it gets used, to optimize the report generation and maximize performance.

Failures
--------
While ``failed`` tells us how many failures occurred, ``failures`` contains a list of what are those failures in the
same order they where registered as dictionaries containing answers to **what**, **why** and **where** that failure
occurred.

Let's analyse this example:

.. code-block:: pycon

    >>> from fastchain import Chain, chainable
    >>> def inverse(num):
    ...     return 1/num
    >>> def handle_failures(report):
    ...     for failure in report['failures']:
    ...         print(failure)
    >>> chain = Chain('test', str.split, '*', (int, '?', inverse, str), chainable(str.join, ' '), log_failures=False)
    >>> chain.add_report_handler(handle_failures, always=True)
    >>> result = chain('1 6 15 ab 0 -20')
    {'source': 'test/sequence[1]/sequence[0]/int', 'input': 'ab', 'error': ValueError("invalid literal for int() with base 10: 'ab'"), 'fatal': True}
    {'source': 'test/sequence[1]/sequence[1]/inverse', 'input': 0, 'error': ZeroDivisionError('division by zero'), 'fatal': False}

And understand what each of those keys means.

Source
~~~~~~
The title of the component that failed, this string can be interpreted to pinpoint exactly
where the failure occurred reducing the debugging time for users to quickly fix issues,
The next section will cover how to read this title.

Input
~~~~~
The value that caused the failure, an interesting peace of information.
While many exceptions point out that value clearly in their messages, not all of them do,
and in addition getting the raw value gives you more insight about analyzing the type:
``type(report['failures'][0]['input'])``.

.. note::

    This is exactly the same input the component got before failing,
    be careful when dealing with larger values kept in memory even
    when they got out of scope.

Error
~~~~~
The exception object that got raised for the failure, an instance of the builtin ``Exception`` subclass,
and it's a useful peace of information that let us know it type, it's value that holds the message
and the traceback.

Fatal
~~~~~
True for failures from required components and False for optional ones,
it tells whether this failure broke the processing sequence and caused a chain failure or it was ignored.

Components title
================
The component title holds information about its location and name relatively to the host chain,
the syntax shares similarities with a file path, that can look like ``<chain>/<node>``,
``<chain>/<collection>[<index>]/<node>``, ``<chain>/<collection>[<index>]/<sub-collection>[<index>]/<node>``,
and so on depending on the chain's structure.
To better understand it we need first to understand how chains recursively parse nodes.

The simplest scenario is a chain with a single node :code:`Chain('single-node', func)`

.. TODO


.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |logging.Logger_docs| raw:: html

   <a href="https://docs.python.org/3/library/logging.html#logging.Logger" target="_blank">logging.Logger</a>
