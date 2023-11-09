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

The error gets completely ignored as the optional node fails, but the error
is not the only thing that gets ignored; the node itself is ignored in a chain or model if it fails.

## Optional nodes in sequences
If a node is marked as **optional** in a chain, the chain tries to run it normally; if the node succeeds, the
chain passes its result to the next one, but if it fails, the chains ignores it and passes the same input to the next one;

````{mermaid}
flowchart LR
    S((star)) --val1--> A[n1]
    A --val2--> B["optional(n2)"]
    B --"SUCCESS: val3"--> C[n3]
    A --"FAIL: val2"--> C
    C --"..."--> E((end))
````

This is useful if a part of chain can fail for a range of inputs, one example can be the following:

````pycon
>>> import re
>>> from funchain import node, optional
>>> get_numbers = node(lambda txt: re.search(r'\d+', txt)) | node(lambda match: match.group())
>>> double = optional(get_numbers, int) | node(lambda x: x*2)
>>> double("The number is 23")  # goes through (get_numbers -> int)
46
>>> double(25)  # skips (get_numbers -> int)
50
````

In this example we created the chain `double` that doubles a number either given in a string or only as a raw number,
the part ``get_numbers → int`` is optional here, it works for strings but fails for numbers, and as it's expected to
fail for numbers in advance, we still want the rest of chain to continue. 

## Optional nodes in branches
If a branch is marked as **optional** in a model, the model runs it normally; if it succeeds, 
the branch's node is replaced with that result, but if it fails, the branch is completely ignored;

Let's make a simple example to see an optional branch in action

````pycon
>>> from funchain import chain, optional
>>> model = chain({'input': (), 'double': lambda x: x * 2, 'next': optional(lambda x: x + 1)})
>>> model(5)
{'input': 5, 'double': 10, 'next': 6}
>>> model('5')
{'input': '5', 'double': '55'}
>>> model(...)
{'input': Ellipsis, 'double': None}
>>> 
````

In the example above we have 3 branches, `input` is a passive node that never fails, `double` which fails for
some types and `next` which is optional.

The optional branch is completely excluded from the last result when it fails, but the normal ones
are still included even if the result is `None` 

````{note}
``optional()`` has the same signature as ``chain()``, it can take multiple inputs and create an optional chains, 
it can take a dictionary or a list and create an optional model, or a single function to create an optional
node.
 
``optional()`` takes a keyword argument ``name``, it does the same as ``chain()``'s ``name``, it labels
the node with a specific name. 
````
