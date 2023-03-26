=========
FunChain
=========

Overview
--------
**FunChain** is an open-source python library that provides tools for chaining and composing functions easily,
it abstracts away and reduces the code needed to validate results (*like* ``None``) and handle exceptions
for individual function call, and isolates each chain call *(sequence of functions' calls)* into its own context
making the main program fault-tolerant.

This library encourages the use of small reusable functions and uses them as building blocks to make more complex
chains *(function pipelines)* all with just a **simple**, **intuitive** and **declarative** syntax,
making the process of **designing**, **maintaining**, **monitoring** and **editing** those chains easier
and less error prone, so developers only focus on the functionality and funchain implements the logic to make it work
automatically.

Audience
--------
This project is aiming python **developers** in general to provide a better development experience.

License
-------
This project is distributed under the MIT license.

.. _installation:

Installation
------------
You can get funchain from PyPI with the following command

.. code-block:: shell

    pip install funchain

To check which version of ``funchain`` is installed in your environment, run the following command

.. code-block:: shell

    pip show funchain


Usage
-----
To get a bit familiar with ``funchain``'s syntax, here's a basic example showing how easy it is to compose functions

.. code-block:: python

    >>> from funchain import node
    >>> def double(num):
    ...     return num * 2
    >>> twice = node(int) | double | str    # composing functions sequentially
    >>> twice("5")
    '10'
    >>> twice("-4")
    '-8'
    >>> twice_all = node(str.split) * twice | ' '.join  # iterating over results
    >>> # same as twice_all = node(str.split) * (node(int) | double | str) | ' '.join
    >>> twice_all('3 7 12 2')
    '6 14 24 4'
    >>> model = {'number': ..., 'double': double, 'half': node(lambda x: x/2) | node(round).partial(ndigits=2), 'pair': lambda x: not x%2}
    >>> model_chain = node(str.split) * (node(int) | model) # complex chain with a collection of nodes
    >>> model_chain('3 2')
    [{'number': 3, 'double': 6, 'half': 1.5, 'pair': False}, {'number': 2, 'double': 4, 'half': 1.0, 'pair': True}]

Fastchain has builtin support for ``async`` functions and callables, the following example shows how easy it is to work with async functions

.. code-block:: python

    >>> from funchain import node
    >>> import asyncio
    >>> async def get_data(id: str) -> str:
    ...     await asyncio.sleep(1)  # mimics the client request IO
    ...     return f"got data for item: {id}"
    >>> request_data = node(str) | get_data
    >>> await request_data(756342)  # takes ~1s to execute
    'got data for item: 756342'
    >>> request_multiple_data = node() * request_data
    >>> await request_multiple_data([2342, 5677, 75634, 23456])  # takes ~1s to execute
    ['got data for: 2342', 'got data for: 5677', 'got data for: 75634', 'got data for: 23456']

More examples will be covered in later chapters.

Versioning
----------
This python package follows the |semver_link| specification, so breaking changes
will only be introduced in MAJOR version bumps (i.e. from ``1.x.x`` to ``2.x.x``).
As long as your app relies on a specific version (i.e. ``1.x.x``), the next MINOR releases will always be
backward compatible.

.. important::

    **funchain** ``0.1.0`` is still currently experimental 🧪, however, it is fully tested.
    Make sure to test it for your specific use case if you plan to integrate it into a production app.

Content
-------
This documentation will walk you through on how to get the best out of ``funchain`` and how it could be
integrated into your application.

This document contains the following pages


.. toctree::
    :includehidden:
    :maxdepth: 2
    :caption: User Guide

    user_guide/getting_started
    user_guide/node_types
    user_guide/node_customization
    user_guide/models
    user_guide/handling_failures
    user_guide/async_support
    user_guide/best_practices


.. |semver_link| raw:: html

    <a href="https://semver.org" target="_blank">semantic versioning</a>
