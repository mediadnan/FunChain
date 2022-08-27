===============
Getting started
===============
In this chapter we will be making our first steps and discover FastChain and its basic API and features,
advance topics will be covered on next chapters.

Installation
============
To start using it we need first to install from PyPI

.. code-block:: shell

   pip install fastchain

However, if you want to test latest features before releases, you can get the newest instance
directly from the Github Repository *(not recommended for production)*

.. code-block:: shell

   pip install git+https://github.com/mediadnan/fastchain.git#egg=fastchain

We can check if the installation went as expected by running :code:`pip show fastchain`,
and after making sure it was correctly installed we can start using it.

Creating a chain
================
The main entrypoint for using fastchain tools is to create a chain object, it can be created the same way one would
create a function that does some processing and then call it.
The difference between having a regular function responsible for performing multiple processing steps and
a chain is that chains treat each step as a unit and keeps track of each one whether it succeeded or not.

A similar behaviour could be achieved in functions wrapping steps that could raise exceptions
in try...except blogs and handle those exceptions in a more specialized manner, that will be more optimized of course,
but for most cases this becomes a constant pattern one wants to automate it.

Basic usage
-----------
To get our hands dirty let's start by an example, our chain will calculates the average from numbers given in string,
more specifically `chain('12.5 56.33 54.7 29.65') -> 38.295`

for that we will be importing a builtin function |statistics.mean_docs| and then import :code:`fastchain.Chain`

.. code-block:: pycon

   >>> from fastchain import Chain
   >>> from statistics import mean
   >>> chain = Chain('my_chain', str.split, '*', float, mean)

The first argument we passed to the chain constructor was its name `'my_chain'`,
let's us skip taking about the rest of arguments as that will be covered in details on the next chapter
and check some few properties of the chain

.. code-block:: pycon

   >>> chain  # the chain representation
   <chain 'my_chain'>
   >>> chain.name  # the chain name
   'my_chain'
   >>> len(chain)  # chain size (str.split, float, mean)
   3

Naming chains is mandatory and helps a lot to identify them from reports when you have many chains,
Now if we want to use our chain all we have to do is call it with the input value

.. code-block:: pycon

   >>> chain('12.5 56.33 54.7 29.65')
   38.295

Perfect, but nothing special about this and it can be achieved in a single line

.. code-block:: pycon

   >>> from statistics import mean
   >>> simpler_chain = lambda numbers: mean(map(float, numbers.split()))
   >>> simpler_chain('12.5 56.33 54.7 29.65')
   38.295

Well sure, but chains are used for cases when the process might fail at any point of the code,
so let's try some few scenarios

.. code-block:: pycon

   >>> chain(['12.5', '56.33', '54.7', '29.65'])
   sequence[0]/str.split raised TypeError("descriptor 'split' for 'str' objects doesn't apply to a 'list' object") when receiving <class 'list'>: ['12.5', '56.33', '54.7', '29.65']

Of course our chain doesn't expect lists, and this example shows that this exception was handled and logged
pointing out the source (syntax will be covered on :ref:`reports chapter <reports>`) the error and the input,
this information is handy when your app hosted that will continue running.

In addition especially when testing, you can tell the chain to print report statistics:

.. code-block:: pycon

   >>> chain = Chain('my_chain', str.split, '*', float, mean, print_stats=True)
   >>> result = chain(['12.5', '56.33', '54.7', '29.65'])
   -- STATS -----------------------------
      success percentage:        0%
      successful operations:     0
      unsuccessful operations:   1
      unreached nodes:           2
      required nodes:            3
      total number of nodes:     3
   --------------------------------------
   sequence[0]/str.split raised TypeError("descriptor 'split' for 'str' objects doesn't apply to a 'list' object") when receiving <class 'list'>: ['12.5', '56.33', '54.7', '29.65']
   >>> repr(result)
   'None'

Lets try another exception in a different step

.. code-block:: pycon

   >>> result = chain('12.5 abc 54.7 29.65')
   -- STATS -----------------------------
      success percentage:        92%
      successful operations:     5
      unsuccessful operations:   1
      unreached nodes:           0
      required nodes:            3
      total number of nodes:     3
   --------------------------------------
   sequence[1]/float raised ValueError("could not convert string to float: 'abc'") when receiving <class 'str'>: 'abc'
   >>> result
   32.28333333333333

Of course logging can be turned off :code:`chain = Chain('chain_name', str.split, ..., log_failures=False)`
and other handlers can be added to handle reports `chain.add_report_handler(my_handler)` (learn more about :ref:`reports <reports>`)
or keep logging but with a custom logger `..., logger='my_logger')`
by passing the name of that logger `'my_logger'` or even passing the logger itself `..., logger=logger)`
if `logger` an instance of the builtin |logging.Logger_docs|


Chain API
---------

.. autoclass:: fastchain.Chain
   :members: name, add_report_handler

.. |statistics.mean_docs| raw:: html

   <a href="https://docs.python.org/3/library/functools.html#functools.partial" target="_blank">statistics.mean</a>

.. |logging.Logger_docs| raw:: html

   <a href="https://docs.python.org/3/library/logging.html#logging.Logger" target="_blank">Logger</a>
