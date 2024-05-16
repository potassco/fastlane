.. _ref_call:

Callables
===========

.. currentmodule:: large_neighbourhood_search

This page will give an overview over all for customizable callables and their interfaces.
For additional information regarding the example implementations, please check :ref:`here<ref_lib>`.

.. _ref_setup:

.. code-block:: python

    setup(lns_object: LNS) -> Tuple[clingo.control.Control, ClingoDLTheory]

Used to initialize clingo.Control objects, reading the seed and setting the additional clingo arguments.
This project includes two example implementations, for clingo (:func:`lib.theory.setup_clingo`)
and clingo-dl (:func:`lib.theory.setup_clingo_dl`) respectively.

.. code-block:: python

    relax(
        model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_parameters: Dict[str, Any]
    ) -> List[Tuple[clingo.symbol.Symbol, bool]]

Used to relax a found model by fixing a subset of atoms.
This project includes two example implementations. A random realaxation (:func:`lib.search.relax_random`)
and a declarative relaxation, where atoms have to be declared available for relaxation through _lns_select/1 and _lns_fix/3 atoms
(:func:`lib.search.relax_declarative`).

.. code-block::  python

    repair(
        lns_object: LNS,
        ctl: clingo.control.Control,
        assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
        thy: Any,
    ) -> bool

Used to repair a set of assumptions to a new model.
This project includes two example implementations, for clingo (:func:`lib.theory.repair_clingo`)
and clingo-dl (:func:`lib.theory.repair_clingo_dl`) respectively.

.. code-block:: python

    calc_opt_value(model: Dict[str, Sequence[clingo.symbol.Symbol]]) -> int

Used to calculate the optimization value of a model.
This project includes one example implementation (:func:`lib.lns_utils.calculate_opt_val`).

.. code-block:: python

    get_first_solution_classic(lns_object: LNS, ctl, thy: Any) -> bool

Used to obtain a first solution/model as a starting point fot LNS.
This project includes two example implementations, one using hard constraints
(:func:`lib.search.get_first_solution_hard_constraint`) and one without them (:func:`lib.search.get_first_solution_classic`).

.. code-block:: python

    check_accept(
        lns_object: LNS,
        new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
        current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    ) -> bool

Used to determine whether a new solution/model is accepted.
This project includes two example implementations, one always accepting
(:func:`lib.search.check_accept_always`) and the other accepting with high enough variability
(:func:`lib.search.check_accept_variability`).

.. code-block:: python

    check_better(
        lns_object: LNS,
        new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
        best_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    ) -> bool

Used to determine whether a new solution/model is better than the current best solution/model.
This project includes two example implementations, one always accepting
(:func:`lib.search.check_better_always`) and the other accepting, if the new solution/model has a lower optimization value
(:func:`lib.search.check_better_classic`).

.. code-block:: python

    better_solution_found(
        lns_object: LNS, ctl: clingo.control.Control
    ) -> None

Tasks performed after a better solution/model was found.
This project includes two example implementations, one for a search using hard constraints
(:func:`lib.search.better_solution_found_hard_constraint`) and one without them (:func:`lib.search.better_solution_found_classic`).

.. code-block:: python

    boundary_handling(lns_object: LNS, action: str) -> bool

Used to define the boundary handling for the LNS. Actions :code:`"init"`, :code:`"update"`,
:code:`"improvement"` and :code:`"no_improvement"` have to be supported.
This project includes one example implementation (:func:`lib.boundary.boundary_overall`).

.. code-block:: python

    check_stop(lns_object: LNS) -> bool

Used to determine whether the search should stop or not.
This project includes two example implementations, one using the number of steps as a criterion
(:func:`lib.boundary.check_stop_steps`) and the other using time (:func:`lib.boundary.check_stop_time`).

.. note::

    :func:`lib.boundary.check_stop_time` is not an exact limit, since the check occurs only between solve calls.
    For a true time limit, a multi-process solution is required.

.. code-block:: python
     
    finish(lns_object) -> None

Tasks performed after the searched finished or is interrupted.
This project includes one example implementation (:func:`lib.boundary.finish`).

.. code-block:: python

    check_stuck(lns_object: LNS) -> bool

Used to determine whether the search is stuck.
This project includes two example implementations, one never returning True
(:func:`lib.search.check_stuck_never`) and the other using the number of steps without improvement
(:func:`lib.search.check_stuck`).

.. code-block:: python

    is_stuck(lns_object: LNS) -> None

Tasks performed after the search is stuck.
This project includes one example implementation (:func:`lib.search.is_stuck`).
