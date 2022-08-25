===================
Designing workflows
===================
FastChain simplifies how process workflows are designed, users describe the structure with python builtin objects
then the chain parses that to internal nodes that pass results from one to another.

In this chapter we will walk through each one of those few options in details and how to define a specific workflow,
but first let's keep in mind that chains are wrappers around our functions and only add functionalities and coordinates
between them and does nothing by its own, and that only functions *(callables in general)* are converted to chain nodes.
With that in mind, nothing prevents us from creating chains with a single node like :code:`Chain('twice', lambda x: x*2)`
but that will only add unnecessary complications for a simple task like this, for this reason we first need to understand
where and when chains are useful.





Chain sequence
==============
Before talking about function composition, we must keep in mind that the most important components for chains are
functions (or any callables) that we give them, and the chain only wraps those functions to add functionalities.

Nothing prevents us from creating a chain with a single function like :code:`Chain('double', lambda x: x*2)`
but that will only add unnecessary complications for a simple task like this.
Chains are made to create data processing pipelines with multiple small reusable functions *(nodes)*
that may fail for specific inputs and need to be handled, and the first use case will be chaining functions in series;


Chain model
===========


Iterating
=========


Optional branches
=================

