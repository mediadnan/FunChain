# Nested nodes

The product of `chain()` or `node()` and other builders is called **node** for a reason, and the reason is that those 
objects _(components)_ can be composed to create other nodes.

+ ``node(function)`` is the simplest node _(leaf or edge node)_, it runs the function inside a context and reports
in case of error

+ ``chain(function1, function2, function3)`` is a chain of nodes ``node(function1)``, 
``node(function2)`` and ``node(function3)``, it calls the first node and then passes its result
to the next if it's successful, but the 'chain' is also a node and can be composed with other nodes
to produce another one

````pycon
>>> from funchain import node
>>> double = node(lambda x: x*2, 'double')
>>> increment = node(lambda x: x+1, 'increment')
>>> increment_double = increment | double  # or chain(increment, double)
>>> increment_double(5)
12
>>> # Reusing `increment_double` in another chain
>>> idd = increment_double | double
>>> idd(5)
24
>>> iddi = idd | increment
>>> iddi(5)
25
````

+ ``chain({'a': function1, 'b': function2})`` produces a model of nodes, the same as ``chain([function1, function2])`` does, 
those models pass their input to each of their branches and return the result as `dict` or `list`. Models are also nodes, 
so they can be composed with more nodes or contain complex branches themselves;

```pycon
>>> model = chain([increment, double])
>>> model(5)
[6, 10]
>>> agg = model | sum
>>> agg(5)
16
>>> model_double = model * double  # doubles each item
>>> model_double(5)
[12, 20]
>>> another_model = chain({
...     'identical': (),    # () means here an empty chain
...     'agg': ([increment, double], sum),  # means a chain with two nodes a model and a function
...     'model_double': model_double    # contains a pre-built model (node in general)
... })
{'identical': 5, 'agg': 16, 'model_double': [12, 20]}
```

The purpose is to demonstrate that all type of nodes share a common interface and can be nested
as much as we need to achieve the required result.