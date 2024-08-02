.. _ref_solv:

.. currentmodule:: large_neighbourhood_search.interfaces.solver

Implementations of :class:`SolverInterface`
============================================

Listed below are multiple solver implementations. A clingo and clingoDL solver using assumptions to fix atoms
and a clingo and clingoDl solver using heuristics instead.

.. currentmodule:: large_neighbourhood_search.__init__

.. note::
    Changes to the solver might also require changes to the :meth:`on_model` method of the :class:`LNS` class.

.. currentmodule:: large_neighbourhood_search.interfaces.solver

ClingoSolver
--------------

Implementation of :class:`SolverInterface` using clingo.
Atoms are fixed using assumptions.

.. automodule:: large_neighbourhood_search.lib.solvers.clingo_solver
    :members:

.. currentmodule:: large_neighbourhood_search.interfaces.solver

ClingoHeuSolver
----------------

Implementation of :class:`SolverInterface` using clingo.
Atoms are fixed using heuristics.

.. automodule:: large_neighbourhood_search.lib.solvers.clingo_heu_solver
    :members:

.. currentmodule:: large_neighbourhood_search.interfaces.solver

ClingoDLSolver
----------------

Implementation of :class:`SolverInterface` using clingo-dl.
Atoms are fixed using assumptions.

.. automodule:: large_neighbourhood_search.lib.solvers.clingo_dl_solver
    :members:

.. currentmodule:: large_neighbourhood_search.interfaces.solver

ClingoDLHeuSolver
------------------

Implementation of :class:`SolverInterface` using clingo-dl.
Atoms are fixed using heuristics.

.. automodule:: large_neighbourhood_search.lib.solvers.clingo_dl_heu_solver
    :members: