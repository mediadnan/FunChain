.. _bigger-projects:

===============
Grouping chains
===============
In bigger projects, we may want to categorize related chains and group them
the same configuration like having the same report handler, keeping the code clean and organized.

For that, FastChain offers a chain factory called :ref:`ChainGroup <fastchain.ChainGroup>` that produces and organizes
related chains

Chains from the same group
==========================

Let's consider that we already have some reusable components:

.. code-block:: python
    :caption: ./toolbox.py

    import json
    import fastchain

    @fastchain.funfact(default='')
    def prepare_url(url_pattern, base_url=None):
        def _prepare_url(id):
            """composes the resource url"""
            ... # code omitted
        return _prepare_url

    @fastchain.funfact(default='')
    def request_data(method='GET', body=None, auth=None, headers=None)
        def _request_data(url):
            """downloads the product markup"""
            ... # code omitted
        return _request_data

    @fastchain.funfact
    def load_json(loader=json.loads, encoding=None):
        def _load_json(data):
            """loads the json data"""
            ... # code omitted
        return _load_json

    ... # code omitted

And we have a collection of chain that gets data from the same source:

.. code-block:: python
    :caption: ./awsome_random_products.py

    from fastchain import ChainGroup
    from .toolbox import *

    base_url = "https://awsome-random-products/api/v2"
    ecom_chains = ChainGroup('awsome_random_products')

    products_chain = ecom_chains('products', prepare_url('/products/{id}', base_url), request_data(), parse_markup(), get_products())
    sellers_chain = ecom_chains('sellers', prepare_url('/sellers/{id}', base_url), request_data(), parse_markup(), get_sellers())
    ...

Now both ``products_chain``, ``sellers_chain`` belong to the same group called *'awsome_random_products'*,
the group name can be observed when interacting with these chains:

.. code-block:: python

    >>> products_chain
    <chain 'awsome_random_products::products'>
    >>> sellers_chain
    <chain 'awsome_random_products::sellers'>

Both chains' names have the same suffix, that can be seen also when accessing ``products_chain.name`` property
or when failures get reported etc...

.. code-block:: python

    >>> products_chain.name
    awsome_random_products::products
    >>> products_chain(None)
    awsome_random_products::products/prepare_url raised TypeError('invalid type for...

And we can get those chains by name directly from the group, if they exist:

.. code-block:: python

    >>> ecom_chains["products"]
    <chain 'awsome_random_products::products'>
    >>> ecom_chains["bla"]
    Traceback (most recent call last):
        ...
    KeyError: "no chain is registered with the name 'bla'"

This gives use the possibility to process data directly from the group

.. code-block:: python

    >>> ecom_chains["products"]('2468885634')
    {'id': 2468885634, 'name': 'Gaming keyboard - KL456', 'price': ...

And For that reason, we can't create two chains with the exact same name:

.. code-block:: python

    >>> products_chain_again = ecom_chains('products', ...
    Traceback (most recent call last):
        ...
    ValueError: "a chain with the same name already been registered"

We can also check whether a chain group contains a specific chain by name:

.. code-block:: python

    >>> 'products' in ecom_chains
    True
    >>> 'bla?' in ecom_chains
    False

If we want chains to be grouped without sharing the same prefix,
we can pass ``prefix=False`` to the ``ChainGroup`` constructor:

.. code-block:: python

    >>> ecom_chains = ChainGroup('awsome_random_products', prefix=False)
    ...
    >>> ecom_chains['products']
    <chain 'products'>

Shared configuration
====================
...