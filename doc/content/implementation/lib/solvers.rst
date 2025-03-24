.. _ref_solv:

.. currentmodule:: mod_lns.interfaces.solver

Implementations of :class:`SolverInterface`
============================================

.. currentmodule:: mod_lns.lns_config

Listed below are multiple solver implementations, which can be used on its own or be modified using an
:class:`LNSConfig` object.

.. currentmodule:: mod_lns.__init__

.. note::
    Changes to the solver might also require changes to the :meth:`on_model` method of the :class:`LNS` class.

.. currentmodule:: mod_lns.interfaces.solver

ClingoSolver
--------------

Implementation of :class:`SolverInterface` using clingo.
By default atoms are fixed using assumptions.

.. automodule:: mod_lns.lib.solvers.clingo_solver
    :members:

.. currentmodule:: mod_lns.interfaces.solver

ClingoDLSolver
----------------

Implementation of :class:`SolverInterface` using clingo-dl.
By default atoms are fixed using assumptions.

.. automodule:: mod_lns.lib.solvers.clingo_dl_solver
    :members:
