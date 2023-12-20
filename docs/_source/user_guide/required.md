# Required nodes
We've seen that the node's default behavior in case of failure is to report and return `None`,
and the optional node gets completely ignored if it fails, but there is an opposite behavior
in case the node holds a **mandatory** operation; this is known as a **required node**.

A required node raises a <a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.FailureException" target='_blank'>`FailureException` [⮩]</a>
in case of failure causing the whole process to stop instead of returning `None`,
this exception needs to be captured at the operation or application toplevel with a
<a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.FailureException" target='_blank'>`Handler` [⮩]</a>
object, this follows the ``failures`` design.

This feature is mostly needed in nested nodes that are required _(expected to success)_, either in chains or models,
because there's no way to mark a failure and break a chained operation other than raising an exception from inside.

But the exception (<a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.FailureException" target='_blank'>`FailureException` [⮩]</a>) 
holds additional details like the source label and the input that caused that failure, and any application should wrap
those operations with the <a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.FailureException" target='_blank'>`Handler` [⮩]</a>
to avoid breaking the entire application.

To demonstrate how can we mark a node as required, here's a simple example

````pycon
>>> from funchain import required, node
````
<div style="text-align: center;"><i>TODO: continue example...</i></div>

## Required node in a sequence

<div style="text-align: center;"><i>TODO: document section...</i></div>

## Required node in a model

<div style="text-align: center;"><i>TODO: document section...</i></div>

