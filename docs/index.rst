=========================
FastChain's Documentation
=========================

Introduction
------------
FastChain is a python based development tool aiming to ease chaining functions by safely
passing results from a function to the next and safely handle error and report it source, input and the error details.

This functionality was originally created as part of a backend web app that processes XML and HTML web content
and provide it in JSON format after a lot of data extraction, parsing and cleaning to provide it as REST API,
and as API consumers may send unexpected data or data providers could change their data structure, this system
had to be robust and handle failures for each unit of its processing pipeline and minimize failure radius
at the same time monitoring and reporting the exact source of failure so it can be quickly fixed by maintainers.
This is where the idea of FastChain came from and the project was separated as an open-source general purpose dependency.

The main goal is to reduce boilerplate code needed for each step to safely process some data
like handling exceptions *(sometimes nesting try...except blocks)*,
branching and decisions making *(nested if...else blocks)* whether to continue or not,
report processing statistics and pinpointing the exact failure details to help debugging.

FastChain is intentionally simple by design, it's a tool not a framework, and that's for the following reasons:

- **Beginner-friendly**: easy to be learned and used by everyone in the great python community,
  staying as close as possible to the regular pythonic syntax.

- **Integrability**: easily integrable with other frameworks and libraries the user is already familiar with,
  and add it as a light tool and why not an extension for one of your favorite frameworks.

- **Single-responsibility**: does a simple task and does it well, lightweight and when developers include
  it as a dependency, they will most likely use all of its features.
  In addition to that, FastChain encourages the use of multiple small functions separately over functions that do
  multiple processing tasks.

- **Independency**: being simple and specialized, it doesn't need too many functionalities that can
  be provided by other third party libraries currently, so it only depends on python's standard libraries.

As well, FastChain is designed to be robust and keep the following standards:

- **Performance**: being as optimized as possible to minimize the impact of added functionalities over
  the processing speed, FastChain maintainers will always have optimization as a priority and will be improved
  or maintained through versions, but in the other hand, FastChain users are expected to follow some advices and
  and :ref:`best-practices` to minimize the performance impact.

- **Abstraction**: offering a declarative and intuitive way for users to describe the process flow structure,
  and the chain takes care of how that structure will be constructed hiding away a lot of complexity and implementation
  details.

- **Isolation**: running each node in isolation so when an error occurs, it only affects that specific branch
  and get reported or if marked optional it could be even ignored in some cases, to avoid breaking the entire system.
  The implementation is a bit simple, the chain uses internal components *(nodes)* that perform a processing
  safely and return a success boolean together with a result (or a default) to let the next node know whether
  to continue processing or stop *(in a railway pattern)*.

- **Monitoring**: being able to keep track of how many nodes have succeeded after each call
  over the total number of nodes, the number of failing and missed ones and a list of reported failures
  if there is any. Each failure holds a copy of the input that caused the failure, the name and location of the component
  that failed and of course a copy of that error.

And finally, it's supposed to give it users the following benefits:

- **DRY**: as previously mentioned, handling errors, checking results, logging, analysing and reporting everywhere
  in your code can be tedious and can become ugly very quickly,
  so having a tool that automates that for you can be handy, especially if the projects changes or scales
  which brings us to the next benefit.

- **Scalability**: process flows can be modified or redesigned a lot easier which makes your project
  easier to grow (quickly, easily and safely) compared if you have to handle everything manually.

- **Flexibility**: chains can be created, modified or redefined with less to worry about introducing bugs
  and with less energy and time compared to what it would've been.

- **Support & Maintenance**: This project is active and updates will be regularly made for optimization,
  features and bug-fixing either discovered by me or anyone using it.

Audience
--------
This library is targeting python developers that do some kind of data processing remotely in particular.

Content
-------
This document contains the following pages

.. toctree::
   :includehidden:
   :maxdepth: 2
   :caption: User Guide

   user_guide/getting_started
   user_guide/designing_workflows
   user_guide/reports
   user_guide/bigger_projects
   user_guide/best_practices
