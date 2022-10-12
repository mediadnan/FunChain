=========================
FastChain's Documentation
=========================

Introduction
============
FastChain is a python based development tool aiming to ease chaining functions and safely
passing results from a function to the next without breaking the whole program,
all while reporting execution statistics and errors.

This library was originally part of a backend web app that gathers and processes XML and HTML web content
and provides clean results as rest API endpoints usually in json format,
and as users may send unexpected data or data providers could change their data source structure,
the backend had to deal with frequent failures and isolate each unit of its processing pipelines
to minimize failure radius and also pinpoint the exact component that failed and the cause of the failure
to allow maintainers quickly fix it.
But soon this idea was separated into its own open-source independent project as it is a general purpose concept.

The main goal of FastChain is to reduce boilerplate code needed to individually handle each data processing step
when composing multiple functions together, and identify the the function that failed and the input that caused it
to reduce the time and energy that needs to be spent debugging.

The library is intentionally simple by design, and that's for the following reasons:

- **Beginner-friendly**: this is intended to be a tool helping developers not another framework that needs to be learned,
  staying as close as possible to the regular pythonic syntax.

- **Integrability**: easily integrable with other frameworks and libraries the user is already familiar with,
  and add it as a light tool and why not an extension for one of your favorite frameworks.

- **Single-responsibility**: does what it needs to do, when one includes it, he will mostly use all its features.

- **Independency**: by being simple and specialized, it doesn't need too many functionalities that can
  be provided by other third party libraries currently, so it only depends on python's standard libraries.

As well, FastChain is designed to be optimal and keep some standards:

- **Performance**: making a tool that eases projects development usually comes with a cost, *impacting performance*,
  and it's impossible to be as performant as a program specifically written and optimized for a specific purpose from scratch,
  for that reason FastChain tries to minimize the impact on performance and resources as possible and it will always be
  aiming towards that. In the other hand, FastChain also provides a guide on how the library is meant to be used,
  in a dedicated chapter called :ref:`best-practices`, The takeaway from that is that performance is a shared responsibility
  between FastChain maintainers and users.

- **Abstraction**: the library offers a declarative and intuitive way for users to describe the processing structure,
  without worrying about the implementation and the coordination between functions.

- **Isolation**: it runs each function in isolation from others so when an error occurs, it only affects that specific branch
  and not the healthy ones, it also gives the possibility to ignore some expected failures.
  This isolation prevents errors from breaking the entire program.

- **Monitoring**: naming components and reporting is a major feature of this library, making it easy to identify
  the chain components from reports (either by statistics reports or failures).
  This can be handy when reading the logs or any kind of notification system.

And finally, it's supposed to give it users the following benefits:

- **DRY**: as previously mentioned, handling errors, checking results, logging, analysing and reporting everywhere
  in your code can be tedious and can become ugly very quickly,
  so having a tool that automates that for you can be handy, especially if the projects changes or scales
  which brings us to the next benefit.

- **Scalability**: process flows can be modified or redesigned a lot easier which makes your project
  easier to grow (quickly, easily and safely) compared if you have to handle everything manually.

- **Flexibility**: chains can be created, modified or redefined with less risk of introducing bugs
  and with less energy and time compared to what it would've been.

- **Support & Maintenance**: the project is active and updates will be regularly made for optimization,
  features and bug-fixing either discovered by me or anyone using it.

Audience
========
FastChain is a tool for composing multiple functions together, it targets python developers that
deal with any kind of data processing in general, and remotely processing web content in particular.

Installation
============
FastChain can be downloaded and installed from Python's package index using the following command:

.. code-block:: shell

    pip install fastchain

Content
-------
This document contains the following pages

.. toctree::
    :includehidden:
    :maxdepth: 2
    :caption: User Guide

    user_guide/getting_started
    user_guide/designing_workflows/index
    user_guide/custom_nodes
    user_guide/reports
    user_guide/chain_groups
    user_guide/best_practices

.. toctree::
    :maxdepth: 2
    :caption: reference

    api_reference
