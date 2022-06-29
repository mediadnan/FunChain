=======
Mapping
=======
The **map option** is needed when you have a function that returns a list, a tuple or any sequence, and you need to apply
the rest of the function to each item of this sequence instead of applying it to the sequence as a whole.
For this fastchain offers an easy syntax to mark where the iterations must begin, and that by passing ``'*'``.

Map option example
------------------
Consider having a string with a sequence of decimals, and we want to get the absolute rounded values.

For this let's create some reusables in a file named ``components.py``

.. literalinclude:: /_examples/components.py
   :caption: components.py
   :language: python
   :lines: 3, 18-25
   :linenos:

And then create ``map_option_example.py`` right next to it

.. _map_option_code_example:
.. literalinclude:: /_examples/map_option_example.py
   :name: map_option_example.py
   :language: python
   :lines: -12
   :linenos:
   :emphasize-lines: 7


In this example, we passed ``split`` as first process of the chain
knowing that it will return a sequence of strings and we need to apply the next functions for each
returned item, so we placed ``'*'`` after ``split``.

Now if we call the chain the result will be

    >>> chain("-134.76 103.4 -89.34")
    (135, 103, 89)

The flow of processes will be represented as follows

.. code-block::

                                                                             | "-134.76" -> [float] =(...)-> [round] => 135
    "-134.76 103.4 -89.34" -> [split_by_commas] => ["-134.76", ...] -> [*] =>| " 103.4 " -> [float] =(...)-> [round] => 103
                                                                             | " -89.34" -> [float] =(...)-> [round] => 89

.. note::
   The chain will fail if the map option\ ``*`` receives a non-iterable object.

Advantages *(Reminder)*
-----------------------

Basically you can achieve the same result by creating a function like this :

.. code-block:: python

   def abs_rounded_values(text: str, sep=','):
       """gets the absolute rounded values from a string of numbers"""
       return (round(abs(float(item))) for item in text.split(sep))

But using a chain instead of function that do it all has better advantages :

1. It gives you **flexibility**, so you can insert, substitute or remove a step in your workflow in one place.

2. It gives you **scalability**, the chain parses its elements recursively, so you can nest and group workflows
as deep as you need, more on that on the next chapter.

3. It gives you **readability**, you can easily visualize and design the structure of your workflow.

4. It gives you **fault tolerance** and **debugging information**, and that is the most important:

Imagine that you have a backend app, and you get ```"534,abc"``` , the app will break when trying to
parse ``'abc'`` into a ``float``, or you need to refactor your functions and add some nested ``try...except``
blocks manually then add specific handlers for each step then attach some callback, maybe add some loggings...,
you see that it gets uglier quickly, and it's far less scalable and more error-prone...

By using the :ref:`fist approach <map_option_code_example>`, this is handled by default, in case of failures like this,
it will return a default value without breaking your code,
and calling your report callback with all the details,
the report callback can be a function that you create, it should get the :ref:`report <report-ref>`
and perform some logic on it, like analysing it, and then dispatching some kind of event *such as sending notifications*.
