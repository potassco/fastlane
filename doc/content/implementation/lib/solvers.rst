.. _ref_solv:

.. currentmodule:: mod_lns.interfaces.solver

Implementations of :class:`SolverInterface`
============================================

Listed below are multiple solver implementations.

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

.. currentmodule:: mod_lns.interfaces.solver

ClingconSolver
----------------

Implementation of :class:`SolverInterface` using clingcon.
By default atoms are fixed using assumptions.

.. automodule:: mod_lns.lib.solvers.clingcon_solver
    :members:
