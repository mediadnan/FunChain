=============================
**FastChain**'s Documentation
=============================

Introduction
============
**FastChain** is a tool aiming to ease piping functions by safely chaining
results from a function to the other **sequentially** or **simultaneously** and reporting failures
without breaking the main program.

It provides tools needed for designing a process pipeline like grouping and branching,
tools for personalizing components' behaviour and properties,
and tools for monitoring the chain process, logging and reporting failures.
All with an easy and pythonic syntax.

**FastChain** was designed for services that need to prepare configuration once *(at start)* and make it ready for use,
in other words, it favours low-latency use over cold-starts. With that in mind when designing your chains it's always
a good practice to completely separate configuration state *(constant process values)* that each function needs
from pure input data that it expects, that will improve the performance of your program for sure.

And for this reason it is recommended and best suited to live
in running container or server instead of a serverless function that only starts when invoked.

Audience
========
This python tools targets python developers in general, any one that does some kind of data processing
or designing process with a series of steps that require validation and reporting might find this
tool useful.

.. warning::
   **FastChain** was developed with Python 3.10 and kept compatibility with Python 3.8 version,
   but the support for those earlier versions will be dropped in next releases.

Need
====
The idea came while working in a project that gathers and analyzes data from public websites and gets a set of values,
usually sources like those are inconsistent and may lead to stopping your main service, and when issues like those occur,
the maintainers need to locate and fix or update that specific part of the service.

Of course there's some other ways to deal with this kind of issues, but as the project grows, it becomes tedious and harder
handling each step of the code separately, or having to dive into the logs to figure out the source of the problem.

The goal of this tool is to reduce or even remove the need to interact with a code each time a provider has changed
the interface or any similar action that may break your code, and to achieve that, ``FastChain`` must:

# Provide an easy API to create a process flow abstracting away all the decisions like ``if..else`` or ```try..except``
  and handle those internally.

# Being able to locate the exact source of problem and report it to a custom handler, decreasing the time to fix it.

# Isolate components to make sure that if one component breaks, the rest will not be affected and continue.

# Separate chain structure from the code entirely, and make it possible to edit the process flows without interacting
  with the core source code.


Pillars
=======
Using ``FastChain`` comes with beneficial advantages, it's built on to of the following pillars:

**Automation**
  Create a process pipline by just passing functions in the desired order
  and you'll get ready to use callable *(chain)*. Piping and creating nodes,
  grouping, branching, error handling and reporting will be handled automatically.
  And passing a value to the chain call, this value will go through all the nodes
  and return the final result.

**Decoupling**
  Create reusable components in a single logical location, or a report handler,
  and use them everywhere lowering code dependency, no function or component
  need to know about the other, and each can be updated without affecting the rest.

**Cohesiveness**
  Encourages you to create functions that have a single responsibility and chain them as units instead
  of chaining a function that has it internal sequence, after all the goal was to isolate process
  steps and identify each node.

**Flexibility**
  Refactoring a sequence is a lot easier and safer, you can easily modify the structure of your process
  flow, combine two, or reuse a part in multiple chains. After all, fewer code is always easier to refactor.

**Scalability**
  Adding more functionality and branching is simpler, you can nest as many structures as you need and design
  complex flows faster.

**Simplicity**
  Providing and easy and intuitive syntax, you don't need to learn a lot to start using it
  because you get what you expect, and it's easier to visualize the process flow by just looking at the structure.

**Typing**
  Encourages you to use annotations *(type hinting)*, you'll get more support, warnings and debugging
  information if you use type hints, but you can still skip it if you want...

**Isolation**
  Each of your functions is converted into a node that runs safely, if it fails *(raises an exception)*
  your main program will not break but only this chain will stop and report the issue.

**Monitoring**
  You can provide a callback function to the chain, it will be called with a report after each time this
  chain is executed, and if any failure occurs the reporter will pinpoint the source and give you detailed information
  about the issue reducing the debugging time and effort. The chain give you the report object and the rest is up to you.

**Performance**
  This library has been developed with performance in mind, and it will always aim for improving it by time
  as long as there is room for better optimization.

**Support**
  This is an actively maintained project, I do rely on it in my personal projects and if there's any discovered
  bug it will soon be fixed. Automated tests will be added from time to time to ensure every use case.
  And if you discover a bug, please let me know.

**Standalone**
  Currently, this project has no third party dependencies that need to be installed, it only relies on the python
  standard libraries, this might change in the future if the project encounters a problem that can be fixed with
  a dependency.

**Integrability**
  It is easy to use it with other libraries and frameworks as it is a thin layer around your functions,
  and it supports either ways of integration, to be integrated in or to integrate other tools.



Documentation content
=====================

.. toctree::
   :includehidden:
   :maxdepth: 2
   :caption: User Guide

   getting_started
   chainables
   design_options/index


.. toctree::
   :maxdepth: 3
   :caption: API Reference

   reference
