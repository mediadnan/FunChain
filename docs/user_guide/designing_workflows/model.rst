.. _chain-models:

=========
The model
=========

.. TODO: rewrite

FastChain simplifies the way we specify the return structure by providing a model of functions with the same structure,
this concept makes it easier and faster to create result models in a very declarative way.

The components covered in this section share one same concept, **branching**, and this is when the component gets
an input it passes it to each of it members and the results are packed into a single structure again.
Unlike how results have been sequentially processed, an input can take multiple paths *simultaneously* for models.

