"""
Components for repairing solutions in the context of LNS.
"""

from logging import Logger
from typing import Optional

from clingo.symbol import Number, Symbol

from mod_lns import Model
from mod_lns.interfaces.solver import Solver, SolverConfig
from mod_lns.lib.components.relaxation import LINE


def repair_assumptions(solver: Solver, solver_config: SolverConfig, fixed_atoms: set[Symbol]) -> Optional[Model]:
    """
    Repair solution by assuming fixed atoms.

    :param solver: Solver instance.
    :type solver: Solver
    :param solver_config: Solver configuration.
    :type solver_config: SolverConfig
    :param fixed_atoms: Set of fixed atoms.
    :type fixed_atoms: set[Symbol]
    :return: New model if found, otherwise None.
    :rtype: Optional[Model]
    """
    return solver.solve(solver_config, list(map(lambda x: (x, True), fixed_atoms)))


def repair_heuristics(
    *,
    solver: Solver,
    solver_config: SolverConfig,
    fixed_atoms_heuristics: set[Symbol],
    prev_fixed_atoms_heuristics: set[Symbol],
    step: int,
    logger: Logger,
) -> Optional[Model]:
    """
    Repair solution by prioritizing fixed atoms.

    :param solver: Solver instance.
    :type solver: Solver
    :param solver_config: Solver configuration.
    :type solver_config: SolverConfig
    :param fixed_atoms_heuristics: Set of fixed atoms for heuristics.
    :type fixed_atoms_heuristics: set[Symbol]
    :param prev_fixed_atoms_heuristics: Set of previously fixed atoms for heuristics.
    :type prev_fixed_atoms_heuristics: set[Symbol]
    :param step: Current step number.
    :type step: int
    :param logger: Logger instance.
    :type logger: Logger
    :return: New model if found, otherwise None.
    :rtype: Optional[Model]
    """
    logger.debug("release externals:")
    # released_externals = []
    for a in prev_fixed_atoms_heuristics:
        solver.release_external(a)
        # released_externals.append(str(a))
    # released_line = ". ".join(released_externals)
    # logger.debug("%s%s", released_line, "." if released_line else "")
    logger.debug(LINE)
    logger.debug("get new externals:")
    statements = ""
    for a in fixed_atoms_heuristics:
        ext_statement = f"#external {a}."
        statements += ext_statement
    # logger.debug(statements)
    logger.debug(LINE)
    solver.add("external", ["t"], statements)
    solver.ground([("external", [Number(step)])])
    solver.ground([("heuristic", [Number(step)])])

    logger.debug("enable externals:")
    # enabled_externals = []
    for a in fixed_atoms_heuristics:
        solver.assign_external(a, True)
        # enabled_externals.append(str(a))
    # enabled_externals_line = ". ".join(enabled_externals)
    # logger.debug("%s%s", enabled_externals_line, "." if enabled_externals_line else "")
    logger.debug(LINE)

    new_model = solver.solve(solver_config)

    return new_model
