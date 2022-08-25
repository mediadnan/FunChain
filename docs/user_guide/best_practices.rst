.. _best-practices:

==============
Best practices
==============
This page contains some advices and and best practices to be followed to take the best out of FastChain features.

Optimization
============

#. **Separate configuration from input value**
    When designing your chains, try to isolate as much as you can configuration values from usage values.
    constant data that will be used in all the calls should be prepared at start (when defining the chain),
    so calls can only depend on the input value. The reason is optimization, reducing the execution time.

    .. code-block:: python3
       
       # Good
       from fastchain import Chain

#. **Use simple functions**
    Creating chains with multiple functions each with a single responsibility
    is better that creating it with less functions that do many things internally.
    After all, FastChain is a tool to isolate and identify the source of failure,
    passing functions with multiple responsibilities is considered an anti-pattern.

.. And note that creating a chain with a single node is considered a misuse and a waist of functionalities *(it is merely allowed for testing and examples purposes)*.

.. pure functions

.. chains are designed *(and supposed)* to be defined globally and be used as functions.
.. So the impact of initialization only happen once your program is run and be ready for usage
.. low-latency use in favour of cold-starts.
.. With that in mind, it is not optimized to use it in systems that start your program each time their called.

Conventions
===========
TODO