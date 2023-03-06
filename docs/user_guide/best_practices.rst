.. _best-practices:

==============
Best practices
==============
To get the best out what ``FastChain`` offers, users need to follow some guidelines to avoid misusing
it and end up with issues instead of benefits.
By making it until this chapter, it should be clear by now why and when to use this FastChain,
but let's make sure to know how to use it.

These best practices are grouped into categories, the order inside the each category doesn't imply the importance.

Caveats
=======
This section covers things to keep in mind to avoid introducing bugs 🪲

Do not Share pre-defined nodes
------------------------------
Unlike functions, dictionaries, tuples, list etc... functions wrapped with ``fastchain.chainable``
are immediately converted into a **node**, and should only be used as ``fastchain.Chain`` parameter.
To get a better understanding about what does this mean, consider this example:

.. code-block:: python3

    from fastchain import Chain

    def some_function(arg):
        # does something

    chain = Chain('some_chain', some_function, some_function)

Here we passed the same function ``some_function`` twice, but the chain parses it into two different nodes
so it can identify which one of them has exactly failed and can control them separately, however
if we do it like this:

.. code-block:: python3
    :caption: BAD

    from fastchain import Chain, chainable

    def some_function(arg):
        """does something"""

    customized = chainable(some_function, name='customized', default='')

    chain = Chain('some_chain', customized, customized)

The chain will treat both ``customized`` as the same node, and this will **lead to bugs** especially in reports,
and the way to address this issue is either using chainable inside Chain like this:

.. code-block:: python3
    :caption: OK

    from fastchain import Chain, chainable

    def some_function(arg):
        """does something"""

    chain = Chain('some_chain',
                  chainable(some_function, name='customized', default=''),
                  chainable(some_function, name='customized', default=''))

Or define a reusable components with ``@fastchain.funfact``

.. code-block:: python3
    :caption: RECOMMENDED

    from fastchain import Chain, funfact

    @funfact(name='customized', default='')
    def some_function():
        def function(arg):
            """does something"""
        return function

    chain = Chain('some_chain', some_function(), some_function())

``some_function()`` will produce a brand-new node each time with the same *name* and *default*.

And make sure not to fall on the same issue again:

.. code-block:: python3
    :caption: BAD

    ...
    customized = some_function()
    chain = Chain('some_chain', customized, customized)

Optimization
============
This section will cover good practices to be adopted for a better optimized usage ✅

Chains should be global
-----------------------
It is recommended to define a chain at module level as chains have two phases **definition** and **usage**,
and the definition phase does some work *(parsing)* that only needs be done once through the lifetime
of the entire program session, so when we define our chains globally, we make sure that the definition is  executed
once when we start the program or when we import it and the chain gets cached and ready to be used.

Hope this abstract example makes the idea clear:

.. code-block:: python3
    :caption: BAD
    :emphasize-lines: 4

    # ... code skipped ...
    @app.get('/items/{id}')
    def get_items(id):
        chain = Chain('items_chain', ...)
        return chain(id)

.. code-block:: python3
    :caption: GOOD
    :emphasize-lines: 2

    # ... code skipped ...
    items_chain = Chain('items_chain', ...)

    @app.get('/items/{id}')
    def get_items(id):
        return items_chain(id)

Cold starts
-----------
As extension to the previous advice, chains are not meant to be used in serverless functions or any
service that makes a fresh start when invoked especially when low latency response is required,
because that will result in additional computation due to the chain preparation and initialization.
A better alternative is to implement code specific to the use case that only does what it should,
or use chains in a running backend.

However, if optimization is not a big concern or/and the system will not be invoked frequently,
chains can be used serverlessly.

Preparing state
---------------
When defining a chain, try to identify values that are constant and values that purely comes from data
that will be processed, the constant values that are independent from data and the common process related
to them does need to be executed each time.

Consider extracting links from a web page using regular expressions:

.. code-block:: pycon

    >>> import re
    >>> from fastchain import Chain, node_factory
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_maker
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_factory
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_maker
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_maker
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_factory
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_maker
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_factory
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_maker
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, node_maker
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))facto
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, nodefac
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
    ['https://justasimpleexample.com/path1',
     'https://justasimpleexample.com/path2',
     'https://justasimpleexample.com/path3']

We can see that everything works as expected, but here
    >>> import re
    >>> from fastchain import Chain, chainable
    >>> from pprint import pp
    >>> markup = """
    ... <html>
    ...     <body>
    ...         <a href="https://justasimpleexample.com/path1">click here</a>
    ...         <a href="https://justasimpleexample.com/path2">click here</a>
    ...         <a href="https://justasimpleexample.com/path3">click here</a>
    ...     </body>
    ... </html>
    ... """
    >>> chain = Chain('my_chain', chainable(re.findall, r'href="(.+?)"', flags=re.DOTALL, name="extract-links"))
    >>> pp(chain(markup))
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