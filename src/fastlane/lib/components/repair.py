"""
Components for repairing solutions in the context of LNS.
"""

from typing import Optional

from clingo.symbol import Number, Symbol

from fastlane import LINE, Model
from fastlane.interfaces.solver import Solver, SolverConfig
from fastlane.utils.logger import DEBUG_EXTRA, LNSLogger


def repair_assumptions(solver: Solver, solver_config: SolverConfig, fixed_atoms: set[Symbol]) -> Optional[Model]:
    """
    Repair solution by assuming fixed atoms.

    :param solver: Solver instance.
    :param solver_config: Solver configuration.
    :param fixed_atoms: Set of fixed atoms.
    :return: New model if found, otherwise None.
    """
    return solver.solve(solver_config, list(map(lambda x: (x, True), fixed_atoms)))


def repair_heuristics(
    *,
    solver: Solver,
    solver_config: SolverConfig,
    fixed_atoms_heuristics: set[Symbol],
    prev_fixed_atoms_heuristics: set[Symbol],
    step: int,
    logger: LNSLogger,
) -> Optional[Model]:
    """
    Repair solution by prioritizing fixed atoms.

    :param solver: Solver instance.
    :param solver_config: Solver configuration.
    :param fixed_atoms_heuristics: Set of fixed atoms for heuristics.
    :param prev_fixed_atoms_heuristics: Set of previously fixed atoms for heuristics.
    :param step: Current step number.
    :param logger: Logger instance.
    :return: New model if found, otherwise None.
    """
    logger.debug(f"release {len(prev_fixed_atoms_heuristics)} externals:")
    released_externals = []
    for a in prev_fixed_atoms_heuristics:
        solver.release_external(a)
        released_externals.append(str(a))

    if logger.isEnabledFor(DEBUG_EXTRA):  # nocoverage
        released_line = ". ".join(released_externals)
        logger.debug_extra("%s%s", released_line, "." if released_line else "")
    logger.debug(f"get {len(fixed_atoms_heuristics)} new externals:")
    statements = ""
    for a in fixed_atoms_heuristics:
        ext_statement = f"#external {a}."
        statements += ext_statement
    logger.debug_extra(statements)
    solver.add("external", ["t"], statements)
    solver.ground([("external", [Number(step)])])
    solver.ground([("heuristic", [Number(step)])])

    logger.debug(f"enable {len(fixed_atoms_heuristics)} externals:")
    enabled_externals = []
    for a in fixed_atoms_heuristics:
        solver.assign_external(a, True)
        enabled_externals.append(str(a))
    if logger.isEnabledFor(DEBUG_EXTRA):  # nocoverage
        enabled_externals_line = ". ".join(enabled_externals)
        logger.debug_extra("%s%s", enabled_externals_line, "." if enabled_externals_line else "")

    logger.debug(LINE)
    logger.debug("start solving...")
    new_model = solver.solve(solver_config)
    # release externals after solving instead of before solving of next iteration
    # for a in fixed_atoms_heuristics:
    #     solver.release_external(a)

    return new_model
