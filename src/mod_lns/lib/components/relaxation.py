"""
Different relaxation methods for LNS.
"""

import random
from logging import Logger  # nocoverage
from typing import Any

from clingo.symbol import Symbol, SymbolType

from mod_lns import Model
from mod_lns.parser.config_parser import ConfigParser
from mod_lns.utils.types import ActiveConfig

LINE = "-" * 50


# unused default relaxation method, can be used for testing
def relax_random(
    model: Model,
    relax_rate: int,
) -> set[Symbol]:
    """
    Relax random number of shown atoms given by the relax_rate.

    :param model: model.
    :type model: Model
    :param relax_rate: Percentage of atoms to relax.
    :type relax_rate: int
    :return: Fixed (not relaxed) atoms.
    :rtype: set[Symbol]
    """
    fixed_atoms = random.sample(sorted(model.shown), round(len(model.shown) * (1 - relax_rate / 100)))
    return set(fixed_atoms)


def format_atoms(atoms: set[Symbol]) -> str:
    """
    Format set of atoms into sorted space-separated string.

    :param atoms: Set of atoms.
    :type atoms: set[Symbol]
    :return: Formatted atom string.
    :rtype: str
    """
    return " ".join([str(atom) for atom in sorted(atoms)])


def _project(
    model: Model, project_operators: list[dict[str, Any]], op_specs: dict[str, set[Symbol]], logger: Logger
) -> set[Symbol]:
    """
    Project atoms based on the runtime configuration.

    :param model: Model containing the atoms.
    :type model: Model
    :param project_operators: List of project operators.
    :type project_operators: list[dict[str, Any]]
    :param op_specs: Operator specifications.
    :type op_specs: dict[str, set[Symbol]]
    :param logger: Logger for debugging.
    :type logger: Logger
    :return: Set of projected atoms
    :rtype: set[Symbol]
    """
    projected_atoms: set[Symbol] = set()

    for project_operator in project_operators:
        projected_atoms.update(ConfigParser.get_projected_atoms(model, op_specs, project_operator["name"]))

    logger.debug(f"{len(projected_atoms)} projected atoms: {format_atoms(projected_atoms)}")
    logger.debug(LINE)

    return projected_atoms


def _destroy_atoms_if_term_selected(
    atom_term_pairs: list[dict[str, Symbol]], percent_or_number: dict[str, Any]
) -> set[Symbol]:
    """
    Randomly select terms by given percentage (or number)
    and return all atoms corresponding to selected terms.

    :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
    :type atom_term_pairs: list[dict[str, Symbol]]
    :param percent_or_number: What percentage (or how many) terms are selected.
    :type percent_or_number: dict[str, Any]
    :return: Destroyed atoms.
    :rtype: set[Symbol]
    """
    candidate_terms = set()
    for pair in atom_term_pairs:
        candidate_terms.add(pair["term"])

    destroyed_atoms = set()
    value = percent_or_number["value"]
    if percent_or_number["type"] == "p":
        num_selected_terms = round(len(candidate_terms) * value / 100)
    else:
        num_selected_terms = min(len(candidate_terms), value)
    selected_terms = random.sample(sorted(candidate_terms), num_selected_terms)
    for pair in atom_term_pairs:
        if pair["term"] in selected_terms:
            destroyed_atoms.add(pair["atom"])

    return destroyed_atoms


# !todo subset of args selected


def _destroy_atoms_if_all_args_selected(
    atom_term_pairs: list[dict[str, Symbol]], percents_or_numbers: list[dict[str, Any]]
) -> set[Symbol]:
    """
    Randomly select arguments based on the specified percentages (or numbers),
    and return all atoms whose terms have all their arguments selected.

    :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
    :type atom_term_pairs: list[dict[str, Symbol]]
    :param percents_or_numbers: What percentages (or how many) arguments are selected.
    :type percents_or_numbers: list[dict[str, Any]]
    :return: Destroyed atoms.
    :rtype: set[Symbol]
    """

    def _is_tuple(term: Symbol) -> bool:
        return term.type == SymbolType.Function and not term.name

    candidate_args: list[set[Symbol]] = [set() for _ in range(len(percents_or_numbers))]
    selected_args: list[list[Symbol]] = []

    for pair in atom_term_pairs:
        if _is_tuple(pair["term"]) and len(pair["term"].arguments) == len(percents_or_numbers):
            for i, arg in enumerate(pair["term"].arguments):
                candidate_args[i].add(arg)

    destroyed_atoms: set[Symbol] = set()
    for i, pn in enumerate(percents_or_numbers):
        value = pn["value"]
        if pn["type"] == "p":
            num_selected_args = round(len(candidate_args[i]) * value / 100)
        else:
            num_selected_args = min(len(candidate_args[i]), value)
        selected_args.append(random.sample(sorted(candidate_args[i]), num_selected_args))
    for pair in atom_term_pairs:
        if _is_tuple(pair["term"]) and len(pair["term"].arguments) == len(percents_or_numbers):
            all_args_selected = all(arg in selected_args[i] for i, arg in enumerate(pair["term"].arguments))
            if all_args_selected:
                destroyed_atoms.add(pair["atom"])

    return destroyed_atoms


def _destroy(
    destroy_operators: list[dict[str, Any]],
    op_specs: dict[str, set[Symbol]],
    projected_atoms: set[Symbol],
    logger: Logger,
) -> set[Symbol]:
    """
    Destroy a subset of atoms according to the runtime configuration.

    :param destroy_operators: List of destroy operators.
    :type destroy_operators: list[dict[str, Any]]
    :param op_specs: Operator specifications.
    :type op_specs: dict[str, set[Symbol]]
    :param projected_atoms: Set of projected atoms
    :type projected_atoms: set[Symbol]
    :return: Set of prioritized atoms
    :rtype: set[Symbol]
    """
    destroyed_atoms: set[Symbol] = set()
    for destroy_operator in destroy_operators:
        atom_term_pairs = ConfigParser.get_atom_term_pairs(op_specs, projected_atoms, destroy_operator["name"])
        if len(destroy_operator["percents_or_numbers"]) == 1:
            destroyed_atoms.update(
                _destroy_atoms_if_term_selected(atom_term_pairs, destroy_operator["percents_or_numbers"][0])
            )
        else:
            destroyed_atoms.update(
                _destroy_atoms_if_all_args_selected(atom_term_pairs, destroy_operator["percents_or_numbers"])
            )

    logger.debug(f"{len(destroyed_atoms)} destroyed atoms: {format_atoms(destroyed_atoms)}")
    logger.debug(LINE)

    prioritized_atoms = projected_atoms - destroyed_atoms

    logger.debug(f"{len(prioritized_atoms)} undestroyed atoms: {format_atoms(prioritized_atoms)}")
    logger.debug(LINE)

    return prioritized_atoms


def relax_config(model: Model, config: ActiveConfig, op_specs: dict[str, set[Symbol]], logger: Logger) -> set[Symbol]:
    """
    Relax portion of atoms as defined by LNS configuration.

    :param config: Active configuration.
    :type config: ActiveConfig
    :param op_specs: Operator specifications.
    :type op_specs: dict[str, set[Symbol]]
    :param logger: Logger instance.
    :type logger: Logger
    :return: Set of heuristic atoms
    :rtype: set[Symbol]
    """
    projected = _project(model, config["project_operators"], op_specs, logger)
    return _destroy(config["destroy_operators"], op_specs, projected, logger)
