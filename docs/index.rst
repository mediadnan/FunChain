=========
FastChain
=========

Overview
--------
**FastChain** is an open-source python library that provides tools for chaining and composing functions easily,
it abstracts away and reduces the code needed to validate results (*like* ``None``) and handle exceptions
for individual function call, and isolates each chain call *(sequence of functions' calls)* into its own context
making the main program fault-tolerant.

This library encourages the use of small reusable functions and uses them as building blocks to make more complex
chains *(function pipelines)* all with just a **simple**, **intuitive** and **declarative** syntax,
making the process of **designing**, **maintaining**, **monitoring** and **editing** those chains easier
and less error prone, so developers only focus on the functionality and fastchain implements the logic to make it work
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
You can get fastchain from PyPI with the following command

.. code-block:: shell

    pip install fastchain

To check which version of ``fastchain`` is installed in your environment, run the following command

.. code-block:: shell

    pip show fastchain

Versioning
----------
This python package follows the |semver_link| specification, so breaking changes
will only be introduced in MAJOR version bumps (i.e. from ``1.x.x`` to ``2.x.x``).
As long as your app relies on a specific version (i.e. ``1.x.x``), the next MINOR releases will always be
backward compatible.

.. important::

    **fastchain** ``0.1.0`` is still currently experimental 🧪, however, it is fully tested.
    Make sure to test it for your specific use case if you plan to integrate it into a production app.

Content
-------
This documentation will walk you through on how to get the best out of ``fastchain`` and how it could be
integrated into your application.

This document contains the following pages


.. toctree::
   :includehidden:
   :maxdepth: 2
   :caption: User Guide

   user_guide/getting_started
   user_guide/best_practices


.. |semver_link| raw:: html

    <a href="https://semver.org" target="_blank">semantic versioning</a>
