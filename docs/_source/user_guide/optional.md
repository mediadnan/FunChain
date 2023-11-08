# Optional nodes
The default behavior for nodes is to report errors and return `None` as an alternative result
in case of failure, this behavior is the same either for single function node like,
a sequence of nodes, or a model branch

```pycon
>>> from funchain import Reporter, node, chain
>>> rep = Reporter('test')
>>> inverse = node(lambda x: 1/x, 'inverse')
>>> decrement = node(lambda x: x-1, 'decrement')
>>> inverse(0, rep('call_1'))  # None

>>> dec_inv = chain(decrement, inverse, name="dec_inc")
>>> dec_inv(1, rep('call_2'))  # None

>>> dec_and_inv = chain({'dec': decrement, 'inv': inverse}, name="dec_and_inv")
>>> dec_and_inv(0, rep('call_3'))
{'dec': -1, 'inv': None}
>>> for failure in rep.failures:
...     print(f'source: {failure.source}\nerror:  {failure.error!r}\n')
...
source: test.call_1.inverse
error:  ZeroDivisionError('division by zero')

source: test.call_2.dec_inc.inverse
error:  ZeroDivisionError('division by zero')

source: test.call_3.dec_and_inv.inv
error:  ZeroDivisionError('division by zero')

```
This is mostly what we need; to avoid exceptions and still report them.
But sometimes when an error is expected, for example, when dealing with unstructured data,
reporting those errors becomes unnecessary and may cause ignoring other important errors that should be reviewed.

And optional node ignores its errors and get ignored if it fails, 
to achieve this we can import [`optional()`](#funchain.optional) from `funchain` and wrap a node with it:

```pycon
...
>>> from funchain import optional
>>> opt_inv = optional(inverse)
>>> rep = Reporter('test')
>>> opt_inv(0, rep)

>>> rep.failures
[]
```

As we have seen, the error gets completely ignored as the optional node fails, but the error
is not the only thing that gets ignored; the node itself is ignored in a chain or model if it fails.

## Optional nodes in sequences

_...TODO_

## Optional nodes in branches

_...TODO_