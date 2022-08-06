================
Designing chains
================

One of the main benefits of using **FastChain** is how simple structures can be defined,
from simple python builtin objects that a chain uses to builds a series of nodes that needed to perform the desired action.

In this chapter we will walk through each of the supported structures, for simplicity, we will call them **chainables**,
and those chainables are:


**function(Any) -> Any**
   Functions *(or any callables)* that take at most only one required positional argument
   are called chainable functions, and those functions are converted to the chain's leaf nodes.
   In fact, a chain **requires** at least one chainable function to be constructed, :ref:`lean more <chain-leaf-nodes>`.

**tuple**
   Tuples of functions or any other supported chainable objects get parsed into a chain sequence,
   where each node passes its result to the next until the last one, we can optionally
   add :ref:`options <chain_options>` before each node, :ref:`lean more <chain_sequence>`.

**dict**
   Dictionaries mapping names to functions or any other supported chainables get parsed into a chain model,
   where the chain uses it as a result model, and calls each function then returns a dictionary with the same
   keys mapping to results, :ref:`lean more <chain_models>`

**list**
   Lists of functions or any other supported chainables get parsed into a chain group, a little sibling
   of the chain model, the chain calls each node and returns the results in the same order, :ref:`lean more <chain_groups>`

**special chainables**
   Other supported chainable types are pre-configured nodes made by fastchain's utility function, 
   like `chainable` or `funfact`.

.. toctree:: 
   :caption: content
   :maxdepth: 1

   nodes
   sequence
   branching
   options
   nesting_structures
