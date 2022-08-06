==============
Best practices
==============

This page contains some advices and and best practices to be followed to take the best out of FastChain features.

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