===============
Getting started
===============

.. functions composition

Installation
============

Installing from PyPI *(recommended)*
------------------------------------
Make sure to download and install FastChain from PyPI to start using it,
and that by running the following command

.. tab-set::

    .. tab-item:: Linux/MacOS
       :sync: unix

       .. code-block:: bash
           
          python3 -m pip install fastchain

    .. tab-item:: Windows
       :sync: windows

       .. code-block:: bat
          
          py -m pip install fastchain

To make sure that the package is installed and available, run the command

.. tab-set::

    .. tab-item:: Linux/MacOS
       :sync: unix

       .. code-block:: bash
           
          python3 -m pip show fastchain

    .. tab-item:: Windows
       :sync: windows

       .. code-block:: bat
          
          py -m pip show fastchain

Installing from repository
--------------------------

.. tab-set::

    .. tab-item:: Linux/MacOS
       :sync: unix

       .. code-block:: bash
           
          python3 -m pip install git+https://github.com/mediadnan/fastchain.git#egg=fastchain

    .. tab-item:: Windows
       :sync: windows

       .. code-block:: bat
          
          py -m pip install git+https://github.com/mediadnan/fastchain.git#egg=fastchain

Create a chain
==============
Chains are the main object of this package, objects that encapsulates a sequence of functions and takes care of piping
results from a function to another isolating potential exceptions that can be raised.

A chain can be defined by creating and instance of fastchain.Chain globally *(module scope)* and be called with
an input argument.



Chain API
=========

.. autoclass:: fastchain::Chain
   :members:
   :special-members: __call__
