.. _reports:

=======
Reports
=======
This chapter will cover chain reports that get generated after each call and hold useful information about
the processing including the failures if there's any. This feature makes it easy to monitor the chain process
and identify the cause and the location of each failure to quickly fix it.
And it is easy to introduce a custom handler to catch reports or even multiple handlers.

Default handler
===============
By default chains come with a **report handler**, the one that logs failures and optionally prints stats.
It uses the standard |logging.Logger_docs| report failures with a level ``logging.ERROR`` for required
nodes' failure *(fatal failures)* and ``logging.INFO`` for optional nodes' failures *(expected failures)*.

.. code-block:: pycon

   >>> from fastchain import Chain
   >>> def always_fails(arg):
   ...     raise ValueError(f"failing for test with {arg}")
   >>> chain = Chain('test', always_fails)
   >>> chain(3)
   test/always_fails raised ValueError('failing for test with 3') when receiving <class 'int'>: 3

We can print statistics too by adding a keyword argument to the definition

.. code-block:: pycon

   >>> chain = Chain('test', always_fails, print_stats=True)
   >>> chain(3)
   -- STATS -----------------------------
      success percentage:        0%
      successful operations:     0
      unsuccessful operations:   1
      unreached nodes:           0
      required nodes:            1
      total number of nodes:     1
   --------------------------------------
   test/always_fails raised ValueError('failing for test with 3') when receiving <class 'int'>: 3


Report interpretation
=====================
.. TODO

.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |logging.Logger_docs| raw:: html

   <a href="https://docs.python.org/3/library/logging.html#logging.Logger" target="_blank">logging.Logger</a>
