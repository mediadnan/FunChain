
# FastChain

[![Tests](https://github.com/mediadnan/fastchain/actions/workflows/tests.yml/badge.svg)](https://github.com/mediadnan/fastchain/actions/workflows/tests.yml)
![Python versions](https://img.shields.io/pypi/pyversions/fastchain)
![PyPI version](https://img.shields.io/pypi/v/fastchain)
![License MIT](https://img.shields.io/github/license/mediadnan/fastchain)

A python3 developers' tool aiming to ease piping functions by passing results from a function to another safely
in a fault-tolerant way, fast, and make reports after each execution.  

## Introduction

**FastChain** does not only provide a way of chaining functions sequentially (**piping**) 
which was the original intention, 
but also provide ways of **branching** *(passing a result to multiple sequences simultaneously)*,
**iterating** *(passing each item of an iterable result to the next function or sequence, something like 'map')*,
**matching** *(passing each item of an iterable result to a corresponding sequence, something like 'strict zip')*,
and **skipping** by making a part of a structure optional and passing its input to the next if it fails.

The goal of this project is to reduce some boilerplate code needed for safely processing any type of data,
like handling exceptions *(nested try...except blocks)*, checking results and make decisions *(nested if...else blocks)*,
report processing statistics and pinpointing the exact source of the failure and its reason easing the debugging process,
the reports are designed to answering questions like 
'how many operations have succeeded or failed?', 'how many required components have succeeded or failed?',
'which is the exact component that failed?', 'what is the exception risen?', 
'what is the value that caused this failure?', and more...

### Philosophy
FastChain is intentionally simple by design, and it's made to be a tool not a framework,
and that's for the following reasons:

- **Beginner-friendly**: by making it easy to be learned and used by everyone in the great python community,
  staying as close as possible to the regular pythonic syntax (*gentle learning curve*). 
  In fact, this project is typed and type-checked so users receive IDE support and warnings when working with it. 
- **Integrability**: by making it easily integrable with other frameworks and libraries the user is already familiar with,
  and add it as a light tool and why not an extension for one of your favorite frameworks.
- **Cohesiveness**: do only what it's expected to do, and do it very well (*single-responsibility principle*). 
  At first, it was tempting to create an events based system where a user can hook handlers to specific signals
  like failures, only to realize after how overly engineered that would've been,
  adding necessary complexity. Instead, functionalities like those
  can be optionally create by the user or handled by third party libraries.
- **Independency**: by being simple and specialized, FastChain doesn't need too much functionality that can be provided
  from another third party libraries currently, so it only depends on python's standard libraries.

As well, FastChain is designed to be robust and keep the following standards:

- **Performance**: by being as optimized as possible to avoid slowing down the processing, and for this reason,
  **chains** are designed *(and supposed)* to be defined globally and be used as functions. 
  So the impact of initialization only happen once your program is run and be ready for usage
  (low-latency use in favour of cold-starts).
  With that in mind, it is not optimized to use it in systems that start your program each time their called. 
- **Abstraction**: by offering a declarative and intuitive api, the user specifies the structure of the process flow,
  and FastChain takes care of how it will be processed, hiding away the complexity and implementation details.
- **Isolation**: running each function in isolation and capture error without breaking other components, or breaking
  the main program. Briefly, if a function raises an exception,
  it will be recorded and inform the next chain functions that it failed.
- **Monitoring**: being able to keep track of how many functions (nodes) have succeeded after each call
  and tell how many were supposed to succeed, record errors, the input that caused them to fail, and the component's
  identifier. to automate monitoring the execution behaviour and call specific handlers for specific conditions,
  reducing the debugging effort.

And finally, it's supposed to give it users the following benefits:

- **Decoupling**: by installing it, the package will be globally available in your project,
  so most of the functionality need will be imported and have a clean code, 
  and in the other hand, FastChain provides a way of creating reusable components import them from
  only one place.
- **DRY**: as previously mentioned, handling errors, checking results, logging, analysing and reporting everywhere
  in your code can be tedious and can become ugly very quickly, 
  so having a tool that automates that for you can be handy, especially if the projects changes or scales
  which brings us to the next benefit.
- **Scalability**: process flows can be modified or redesigned a lot easier which makes your project
  easier to scale (quickly) compared if you have to handle everything manually.
- **Flexibility**: chains can be created, modified or redefined with less to worry about introducing bugs 
  and with less energy and time compared to what it would've been.

### Audience
This project is targeting python developers in general, and developers that do any kind of data processing in particular.


## Installation
It is of course 
### Install from pypi
Make sure to install this package to use it, via this command
````shell
pip install fastchain
````
Check that you have the last version installed, by running this command
````shell
pip show fastchain
````
### Get source code
FastChain is actively developed on GitHub, you can get the latest instance
directly from the repository via this command:
````shell
pip install git+https://github.com/mediadnan/fastchain.git#egg=fastchain
````


(uncompleted README file)