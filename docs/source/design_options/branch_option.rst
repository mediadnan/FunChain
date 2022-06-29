=========
Branching
=========
This option is useful when you get to a step that needs to be branched, in other words multiple sub-chains depends on
the same previous result, each branch should have a unique name, the syntax for this is a ``{}``
that maps branches' names ``str`` to a **chainable function**, a group of chainables, a dictionary of the same times
or any other supported option...

You can achieve this by providing a dictionary of instructions (called Chain model) and getting back a dictionary of results.


Branching option example
------------------------
Let say we have a string containing a sequence of numbers and we want to perform some statistics on them.

We'll use the previously defined ``split``

.. literalinclude:: /_examples/components.py
   :caption: components.py
   :language: python
   :lines: 20-25
   :lineno-start: 20

And create a new file ``branching_option_example`` then define our chain

.. literalinclude:: /_examples/branching_option_example.py
   :caption: branching_option_example.py
   :language: python
   :lines: -17
   :linenos:
   :emphasize-lines: 9-15

Now if we test it the result will be as follows

    >>> chain("1, 2, 4, 3, 2, 4, 0, 1, 8, 9, 0, 1, 4, 2, 1, 2, 2, 4, 1, 0, 6")
    {'max': 9, 'min': 0, 'mode': 1, 'mean': 3, 'median': 2}

If everything goes without failing, the process flow will be like the following

.. code-block::

                                                        max   : (1, 2, ...) -> 9                       |
                                       | '1'  -> 1 |    min   : (1, 2, ...) -> 0                       |
   "1, 2, ..."  -> ["1", " 2", ...] -> | ' 2' -> 2 | -> mode  : (1, 2, ...) -> 1                       |-> {'max': 9, ...}
                                       |    ...    |    median: (1, 2, ...) -> 2                       |
                                                        mean  : (1, 2, ...) -> 2.7142857142857144 -> 2 |

.. note::
    If a failure occurs outside the model, the error will be reported under the chain title *(e.g* ``analyze_numbers :: ...``\ *)*

    But if it occurs inside the model, it will be reported under the branch title
    *(e.g* ``analyze_numbers / mean :: ...``\ *)*\ .
