.. raw:: html

    <style> .red {color:red} </style>

.. role:: red

.. _getting-started:

===============
Getting started
===============
In this chapter we see some basic usage of FastChain, and test it
in various case scenarios to get the main concept.

Please make sure to read carefully this chapter before moving to
the next once.

Installation
============
Pip install
-----------
Make sure to install this package to use it, via the command

.. code-block:: shell

   $ pip install fastchain

To check if the right version was installed run

.. code-block:: shell

   $ pip show fastchain

Source code
-----------
FastChain is actively developed on Github, you can get the latest instance
directly from the repository via this command

.. code-block:: shell

   $ git clone git://github.com/mediadnan/fastchain.git

______________

Basic usage
===========
This package contains some funny names that you'll get used to, but when you read **'chainable function'**
that means a functions that takes exactly one positional argument *(or one positional first argument and optional others)*
and returns a value, that value will be the input for the next **chainable function** and so on...
Basically, chainable functions are functions with a signature ``(Any) -> Any``

The main objects that we will be interacting with are :ref:`Chain <chain-ref>` instances, so let create a chain,
as example let say that we want to calculate the rounded square root of a number given as a string.

.. _rounded_square_root_example:
.. literalinclude:: /_examples/rounded_square_root_example.py
   :language: python
   :linenos:
   :name: rounded square root example

In the example above we created a :ref:`chain <chain-ref>` with a sequence of three functions (``float`` -> ``sqrt`` -> ``round``)
and gave it the title ``rounded_square_root`` and we specified ``print`` as the report handler,
when we call it with ``"   17  "``, the input will be processed as follows:

    "   17  " -> **[float]** => 17.0 -> **[sqrt]** => 4.123105625617661 -> **[round]** => 4

.. note::
    *In fact this is overly simplified for example purposes, stripping out the decision nodes...*

The chain will also report that ```3``` operations succeeded and ```0``` failed through the :ref:`report <report-ref>`.

In fact, we passed the builtin ``print`` function as callback,
the report will be printed to the standard output like this:

.. code-block:: console

    ================================================================================
    REPORT: 'rounded_square_root'
    SUMMARY: all components have succeeded
        3 completed components (3 completed operations)
        0 failed components (0 failed operations)
    ================================================================================


Now if we call this :ref:`chain <rounded_square_root_example>` with an invalid string like ``"a34"``
it will fail at the first function :

    "a34" -> **[float]** :red:`!! "ValueError: could not convert string to float: 'a34'"` => None

This time it will report **O** operations succeeded and **1** failed, the :ref:`report <report-ref>` will contain
all the information in case of failure such as the exception object itself (*Exception type, exception message and traceback ...*) ,
the full title of the failing component *(function)* in this case it will be ``'rounded_square_root :: float (0, 0)'``,
it follows this pattern ``[chain's name] :: [component's name] [absolute position]`` and ``(0, 0)`` means the first component
on the main sequence, the given input, the returned output, the root and the previous components.

This time the console output will be like :

.. code-block:: console

    ================================================================================
    REPORT: 'rounded_square_root'
    SUMMARY: no component has succeeded
        0 completed components (0 completed operations)
        1 failed components (1 failed operations)
    --------------------------------------------------------------------------------
    FAILURES:
      rounded_square_root :: float (0, 0):
        - input: 'a34'
          output: None
          error: ValueError("could not convert string to float: 'a34'")
          root: '([float(?) -> ?] => [sqrt(?) -> ?] => [round(?) -> ?])'
          previous: 'None'
    ================================================================================

There might be other failing scenarios for example if we pass ``"-5"`` to  our
:ref:`chain <rounded_square_root_example>`, the sequence will be like:

    "-5" -> [float] => -5.0 -> [sqrt] :red:`!! "ValueError: math domain error"` => None

And that will report **1** operation has succeeded and **1** has failed.

____

Next, we'll take about personalizing a chainable function with :ref:`chainable <chainable-ref>` and :ref:`funfact <funfact-ref>`
decorators...
