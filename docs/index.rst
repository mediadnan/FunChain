=========
FunChain
=========

Overview
--------

**FunChain** is an open-source python library that provides tools for composing functions,
it abstracts away and reduces the code needed to create a function pipeline that processes an input sequentially,
or processes it through multiple branches in isolation to avoid that an exception *(failure)* from a branch
to affect the entire chain.

To achieve this behavior, ``funchain`` uses a python library called `failures` to gather and report labeled exceptions
throughout the chain call.

This library encourages the use of small reusable functions as components and uses them as building blocks to make more
complex chains, with a **simple**, **intuitive** and **declarative** syntax,
making the process of **designing**, **maintaining** and **monitoring** those chains easier and less error prone,
so developers only focus on the functionality and ``funchain`` implements the logic to make it work automatically.

Motivation
----------

Programing in general consists of a series of instructions that get executed one after the other, and when an instruction
fails or returns an unexpected result, that causes all the remaining instructions that depends on it to fail.

But there are many solution to that out there for that issue, some programing languages *like JavaScript, Dart, Swift ...*
have the concept of optional chaining that prevent type errors like ``obj?.attribute``, Others give
developers the responsibility to check results before passing them to the next instruction, and also we have
great design patterns to follow *(especially in functional programming paradigm)* that target this specific issue
*(like Monad and Railway oriented programming...)*. But for lazy programmers like myself, bending an entire code base
to match a specific design pattern or handle each function separately is definitively not what I want to do,
however in production we never want our application to go down if one part fails or if that fails for a specific input,
usually we make sure to wrap each part and handle it exceptions and either simply logging them or sending them
to a remote logging server, store and analyse them.

FunChain is designed to automate and simplify this process and to give a better developer experience, by taking care
of what happens between each step *(node)* and how each failure should be handled, and simplifies the definition of
function pipelines with a declarative, intuitive and easy syntax.

In this chapter we will discover the basic use case of ``funchain`` and make our first steps,
the next chapters will be covering specific and advanced topics in depth.

Audience
--------
Anyone working on a python project that requires processing data through multiple functions and needs to isolate
each step and report errors with labels and details **can** benefit from the tooling offered by this library,
using it may reduce boilerplate code and code repetition.

Continue reading the documentation to find out if ``FunChain`` offers tools that you need
or aligns with your design pattern.

License
-------
This project is distributed under the MIT license.

.. _installation:

Installation
------------
You can include ``FunChain`` into your environment using this command

.. code-block:: shell

    pip install funchain


Versioning
----------
This python package follows the |semver_link| specification, so breaking changes
will only be introduced in MAJOR version bumps (i.e. from ``1.x.x`` to ``2.x.x``).
As long as your app relies on a specific version (i.e. ``1.x.x``), the next MINOR releases will always be
backward compatible.

.. important::

    **funchain** ``0.1.0`` is still currently experimental 🧪, however, it is tested.
    Make sure to test it for your specific use case if you plan to integrate it into a production app.

*TODO: documentation*


.. |semver_link| raw:: html

    <a href="https://semver.org" target="_blank">semantic versioning</a>
