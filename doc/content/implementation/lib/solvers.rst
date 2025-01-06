.. _ref_solv:

.. currentmodule:: mod_lns.interfaces.solver

Implementations of :class:`SolverInterface`
============================================

Listed below are multiple solver implementations. A clingo and clingoDL solver using assumptions to fix atoms
and a clingo and clingoDl solver using heuristics instead.

.. currentmodule:: mod_lns.__init__

.. note::
    Changes to the solver might also require changes to the :meth:`on_model` method of the :class:`LNS` class.

.. currentmodule:: mod_lns.interfaces.solver

ClingoSolver
--------------

Implementation of :class:`SolverInterface` using clingo.
Atoms are fixed using assumptions.

.. automodule:: mod_lns.lib.solvers.clingo_solver
    :members:

.. currentmodule:: mod_lns.interfaces.solver

ClingoHeuSolver
----------------

Implementation of :class:`SolverInterface` using clingo.
Atoms are fixed using heuristics.

.. automodule:: mod_lns.lib.solvers.clingo_heu_solver
    :members:

.. currentmodule:: mod_lns.interfaces.solver

ClingoDLSolver
----------------

Implementation of :class:`SolverInterface` using clingo-dl.
Atoms are fixed using assumptions.

.. automodule:: mod_lns.lib.solvers.clingo_dl_solver
    :members:

.. currentmodule:: mod_lns.interfaces.solver

ClingoDLHeuSolver
------------------

Implementation of :class:`SolverInterface` using clingo-dl.
Atoms are fixed using heuristics.

.. automodule:: mod_lns.lib.solvers.clingo_dl_heu_solver
    :members: