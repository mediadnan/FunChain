=========
Branching
=========
This option is useful when you get to a step that needs to be branched, in other words multiple sub-chains depends on
the same previous result, each branch should have a unique name, the syntax for this is a ``dict``
that maps branches' names ``str`` to a chainable function, group of chainables, a dictionary or any other supported option...

You can achieve this by providing a dictionary of instructions (called Chain model) and getting back a dictionary of results.
