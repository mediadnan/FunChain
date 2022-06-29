========
Grouping
========

This option is used for grouping a sequence of chainable functions, by default there is only one group, the main group,
and it's the sequence we provide to the ``Chain``. But in some cases we might need subgroups, and to do so
we surround the chainables by ``()``.

Group option example
--------------------
Sub-grouping is mostly needed to mark an end for a mapped sequence.

Let add some reusables

.. literalinclude:: /_examples/components.py
   :caption: components.py
   :language: python
   :lines: 20-41
   :lineno-start: 20

Then create our chain

.. literalinclude:: /_examples/group_option_example.py
   :caption: group_option_example.py
   :language: python
   :lines: 1-11
   :emphasize-lines: 7
   :linenos:

And if we test it, test it the result will be

    >>> chain("text-1 text-2 text-3")
    <div><p>text-1</p><p>text-2</p><p>text-3</p></div>

As we used ``()`` the process flow will be like

.. code-block::

                                          |-> [str.strip] -> [add_div_tag] |
    (start) -> [split_articles] -> [*] -> |-> [str.strip] -> [add_div_tag] |-> [join_articles] -> [add_main_tag] -> (end)
                                          |-> [str.strip] -> [add_div_tag] |

If we didn't use parenthesis the elements won't join.

Here's how it would've been **without** ``()``

.. code-block::

                                          |-> [str.strip] -> [add_div_tag] -> [join_articles] -> [add_main_tag] |
    (start) -> [split_articles] -> [*] -> |-> [str.strip] -> [add_div_tag] -> [join_articles] -> [add_main_tag] |-> (end)
                                          |-> [str.strip] -> [add_div_tag] -> [join_articles] -> [add_main_tag] |


.. note::
   Grouping is also required when branching a sequence, the next chapter makes use of that.

