# Required nodes
We've seen that the node's default behavior in case of failure is to report and return `None`,
and the optional node gets completely ignored if it fails, but there is an opposite behavior
in case the node holds a **mandatory** operation; this is known as a required node.

A required node raises a <a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.FailureException" target='_blank'>`FailureException` [⮩]</a>
in case of failure causing the whole process to stop instead of returning `None`,
this exception needs to be captured at the operation or application toplevel with a
<a href="https://failures.readthedocs.io/en/latest/api_ref.html#failures.FailureException" target='_blank'>`Handler` [⮩]</a>
object, this follows the ``failures`` design.

---

<div style="text-align: center;"><i>TODO: continue documentation..._</i></div>