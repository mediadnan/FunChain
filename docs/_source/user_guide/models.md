# Funchain Models
A model in `funchain` is a structure of nodes _(`dict` or `list`)_ that specifies the structure of the result,
same as a chain, it is composed of multiple other nodes, but the main difference is that is takes an input
and passes it to multiple _(parallel)_ branches.

If we consider the following chain ``cn = chain(fun1, fun2, fun3)``, it processes the input sequentially 
like the following

```{mermaid}
:align: center

flowchart LR
    I((input)) --> A
    A[fun1] --> B
    B[fun2] --> C[fun3]
    C --> E((output))
```

However, a list-model like ``lm = chain([fun1, fun2, fun3])`` processes the input _simultaneously_ and can be visualized
like the following

```{mermaid}
:align: center

flowchart LR
    I((input)) --> A[fun1] --> E
    I --> B[fun2] --> E
    I --> C[fun3]
    C --> E((output))
```
```{note}
The word simultaneously here is not in the context of parallel computing, it means that the same input is processes
through multiple branches, or _(in async nodes)_  the input is processed asynchronously through multiple
branches.
```

## Dict model
The `dict`-model is a node defined by a dictionary of nodes and returns the same structure as a result,
this example shows how a dict-model is created and how it works:

{emphasize-lines="14-17"}
````python
from json import loads
from funchain import chain, node, BaseNode

json_data = '{"personal-info": {"name": "adam", "age": 30}, "title": "developer"}'

def getitem(key: str) -> BaseNode:
    """Gets an item from dict by key"""
    def get(data: dict):
        return data[key]
    return node(get, name=f"get-{key}")

dict_model = chain(
    loads,
    {
        'name': getitem('personal-info') | getitem('name') | node(str.title),
        'profession': getitem('title')
    }
)
````
If we test it in our python terminal, we'll get this 
```pycon
>>> dict_model(json_data)
{'name': 'Adam', 'profession': 'developer'}
```
Our model ``{'name': getitem('personal-info') ..., 'profession': getitem('title')}`` 
resulted in ``{'name': 'Adam', 'profession': 'developer'}``.

This syntax is very declarative and serves as a template for the result.
```{important}
The model can be defined and compiled using ``chain()``, ``loop()`` or any other builder, **but not ``node()``**,
as ``node()`` only takes functions and callables in general.
```
The dict-model automatically names its branches with the given key, and that key is concatenated to the label in case
of failure;
```pycon
>>> data = {'name': "Adam", 'age': 30}
>>> model = chain({'name': getitem('nam'), 'age': getitem('age')})
>>> reporter = Reporter("bad_key_test")
>>> model(data, reporter)
{'name': None, 'age': 30}
>>> reporter.failures
[Failure(source='bad_key_test.name.get-nam', error=KeyError('nam'), details={'input': {'name': 'Adam', 'age': 30}})]
```

## List model
The `list`-model is similar to a `dict`-model in terms of behavior, the only difference is that 
a list-model returns a list of result instead of a dictionary.

````pycon
>>> from funchain import chain
>>> model = chain([lambda x: x - 5, lambda x: x + 5], name="interval")
>>> model(25)
[20, 30]
>>> model(-2)
[-6, 3]
````