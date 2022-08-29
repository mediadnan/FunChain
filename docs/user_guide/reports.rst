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
   

Setting a report handler
========================
The default logging handler can be enough for simple use cases, but it's not always the desired action to report failures

.. TODO: finish the docs

Report interpretation
=====================
.. TODO

.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |logging.Logger_docs| raw:: html

   <a href="https://docs.python.org/3/library/logging.html#logging.Logger" target="_blank">logging.Logger</a>
