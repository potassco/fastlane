Usage
============

This project allows a multitude of options to customize the search. For a list of all possible options run:

.. code-block:: console

    $ large_neighbourhood_search -h


For complete control of search parameters, a parameter file has to be used. An example of such parameter file can be created at the target 
directory using:

.. code-block:: console

    $ large_neighbourhood_search --gen-example DIR


A new parameter file in the target directory can be created using:

.. code-block:: console

    $ large_neighbourhood_search --new-param-file DIR

The following search parameters can be set using a parameter file:
 * **Name**: :code:`string`, name of the parameter file.
 * **Relaxation mode**: :code:`decl|rndm`, use declarative or random selection of relaxation atoms. If using declarative mode see :ref:`decl-mode`.
 * **Relax rates**: :code:`float+`, one or more relax rates for LNS. Value between 0 and 1.
 * **Relax threshold**: :code:`positive integer`, if more than 1 relax rate, after how many failures to find better solutions a new relax rate should be selected.
    Always the next rate in the relax rate list is selected.
 * **Search mode**: :code:`hard_const|classic`, search mode used for LNS. Enforcing better solutions during solving via hard constraints or not (classic).
 * **Bound mode**: :code:`overall|per_improv`, stop LNS after overall bound is reached or no better solution as be found in the given bound.
 * **Bound type**: :code:`steps|time`, bound value is to interpreted as number of steps or time in seconds.
 * **Bound value**: :code:`positive intger`.
 * **Seed**: :code:`positive integer`, seed for LNS, e.g. random relaxation.
Example
-------

An example call for LNS using hard constraints in declarative mode with a constant relax rate of 0.4  on the provided social golfer example would look like this:

.. code-block:: console

    $ large_neighbourhood_search -i ./examples/golf.lp --declarative --relax-rate 0.4 

Problem instances have to contain :code:`_minimize/2` predicates to describe optimization criteria. 
:code:`_minimize(N,O)` sates, that each occurrence of :code:`O` corresponds to an optimization value of N.

.. _decl-mode:

Declarative mode
----------------

When using declarative mode to be relaxed atoms have to be selected using :code:`_lns_select/1` and optionally a subset fixed using :code:`_lns_fix/2`.
An example can be found in :file:`./examples/golf.lp`

