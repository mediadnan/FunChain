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
