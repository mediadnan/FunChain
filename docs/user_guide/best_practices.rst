==============
Best practices
==============
To get the best out of FastChain, this section helps you with some good practices to follow,
some of them are performance related and others are about conveniance and quality.

Optimization
============
Make chains global
------------------
When we define chains, fastchain runs some code to build a callable object with the right features,
this code is most of the time recursive and involves some validation and inspection.
So the those FastChain objects have to main phases, **definition** and **usage**, the definition
should only execute once per program session, and then the objects are cached and ready for use for 
multiple times.

For that reason, it is recommended to define chains globally *at module level* and not inside
some function that runs multiple times.

.. code-block:: python
    :caption: BAD
    :emphasize-lines: 4

    # some code here ...

    def get_item(item_id: int) -> Item:
        items_getter = node(lambda id: request.get(f'https://example.com/items/{id}'), name='request_get') | json.parse | Item
        return items_getter(item_id)

This code will define ``items_getter`` each time ``get_item()`` is called, the impact of the chain definition
will add up and may slow your program.

To make sure this doesn't happen, we define ``items_getter`` outside at module level, like this:

.. code-block:: python
    :caption: GOOD 
    :emphasize-lines: 3

    # some code here ...

    items_getter = node(lambda id: request.get(f'https://example.com/items/{id}'), name='request_get') | json.parse | Item

    def get_item(item_id: int) -> Item:
        return items_getter(item_id)


Cold starts
-----------
Extending the previous advice, if your program runs every time it gets called, like a CLI or
in a serverless cloud function ..., you might run into the same situation where the definition
is run each time the program is called and might have impact on performance,
the impact might be ignorable for less complex structures.

Preparing chains
----------------
When we define chains, it's necessary to classify inputs into two categories, the ones that
are related to the chain itself and others that purely come from the caller,
the ones that that are related to the chain and should be shared between calls
should be partially applied and prepared to optimize the performance.

To give an example, let's consider a chain that will be extracting links from a web page using regular expressions:

.. code-block:: python
    :caption: BAD

    import re
    from fastchain import node
    
    markup = """
        <html>
        <body>
            <a href="https://justasimpleexample.com/path1">click here</a>
            <a href="https://justasimpleexample.com/path2">click here</a>
            <a href="https://justasimpleexample.com/path3">click here</a>
        </body>
        </html>
    """
    get_links = node(re.findall, r'href="(.+?)"', flags=re.DOTALL)
    
    pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here :regexp:`href="(.+?)"` is compiled
every time ``my_chain`` is called while it can be compiled once and used many times which is
more optimized.

And to achieve that we define a reusable regex.findall component

.. literalinclude:: ../examples/regex-component.py
   :caption: components.py
   :emphasize-lines: 7, 9

And use it like this

.. code-block:: pycon

    >>> from pprint import pp
    >>> from fastchain import Chain
    >>> from components import regex_findall
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', regex_findall(r'href="(.+?)"'))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We get the same result but now the pattern is compiled once, this optimizes resources usage and
result in a faster processing.

.. note::

   The previous example is not practical and there are libraries best suited to extract data from
   markups HTML/XML like |lxml|, |beautifulsoup|, |parsel| and |scrapy| just to name a few.

.. _optimization_beware_of_report_handling:

Beware of report handling
-------------------------
When setting custom handlers to a chain, we must keep in mind that those handlers will all be called
**before returning the result**, and it's easy for us to slow down the chain performance.
To better get an idea, go and try this

.. literalinclude:: ../examples/slow_report_handling.py
   :language: python

Even while ``lambda x: x`` should be instantaneous, the chain took about 2s to return the same input.
With that in mind, we have two options to fix this:

+ If the consumer needs the result as soon as it gets generated, the report handler should either store
  the report somewhere to be interpreted after delivering the result or interpret it in the
  background *(a different thread or process ...)*

+ If the report needs to be analysed before returning the result *(maybe for a decision making)*, the handler
  should be optimized as much as possible to match the expected performance.

Conventions
===========
This sections will cover tips about the ideal usage of ``FastChain`` and mistakes to avoid 💡

Use chains to simplify
----------------------
The main goal of this library is to simplify the creation of pipelines, however creating a chain with a single function
will only add unnecessary complications. Any thing that could be achieved more easily without ``FastChain`` should
be achieved without it, knowing that nothing prevents us from creating this :code:`Chain('twice', lambda x: x*2)`
*which ironically enough is what we've been doing through this guide*, but this is merely allowed for testing or examples
and it will only add unnecessary complications and obscure our code for other especially when having no intention
to handle failures.

Use simple functions
--------------------
It is always recommended to define chains with multiple small specific functions that do only one thing
*(single responsibility principle)* over using fewer more complex functions, this advice is not exclusive
to ``FastChain`` but it is a good practice in general, it increases re-usability, simplifies testing, separation
of concerns, increases cohesiveness... But particularly when we define a chain with *'monolithic'* functions
that contain internal pipelines we are missing the whole point about chains and it's considered an anti-pattern,
it's good to remember that their main strength is the isolation of each processing step.


Use pure functions
------------------
Use pure functions that always return the same result for the same input, without side effects
like changing state from an outer scope or **mutating the input**, this might potentially cause issues especially
when when branching, as the same input is taken by multiple functions and mutating it in one place affects
the other functions. Unless of course, your intentionally want to mutate it and that will not affect anything
in your workflow.

.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |lxml| raw:: html

   <a href="https://lxml.de/" target="_blank">lxml</a>

.. |beautifulsoup| raw:: html

   <a href="https://www.crummy.com/software/BeautifulSoup/bs4/doc/" target="_blank">BeautifulSoup</a>

.. |scrapy| raw:: html

   <a href="https://docs.scrapy.org/en/latest/" target="_blank">Scrapy</a>

.. |parsel| raw:: html

   <a href="https://parsel.readthedocs.io/en/latest/usage.html" target="_blank">Parsel</a>