"""
Different destruction methods for LNS.
"""

import random
from logging import Logger  # nocoverage

from clingo.symbol import Symbol, SymbolType

from mod_lns import Model
from mod_lns.parsers.config_parser import ConfigParser
from mod_lns.utils.types import ActiveConfig, DestroyOperator, DestructionSpec, ProjectOperator

LINE = "-" * 50


# unused default destruction method, can be used for testing
def destroy_random(
    model: Model,
    destruction_rate: int,
) -> set[Symbol]:
    """
    Destroy random number of shown atoms given by the destruction_rate.

    :param model: model.
    :param destruction_rate: Percentage of atoms to destroy.
    :return: Fixed (not destroyed) atoms.
    """
    fixed_atoms = random.sample(sorted(model.shown), round(len(model.shown) * (1 - destruction_rate / 100)))
    return set(fixed_atoms)


def format_atoms(atoms: set[Symbol]) -> str:
    """
    Format set of atoms into sorted space-separated string.

    :param atoms: Set of atoms.
    :return: Formatted atom string.
    """
    return " ".join([str(atom) for atom in sorted(atoms)])


def _project(model: Model, project_operators: list[ProjectOperator], logger: Logger) -> set[Symbol]:
    """
    Project atoms based on the runtime configuration.

    :param model: Model containing the atoms.
    :param project_operators: List of project operators.
    :param logger: Logger for debugging.
    :return: Set of projected atoms
    """
    projected_atoms: set[Symbol] = set()

    for project_operator in project_operators:
        projected_atoms.update(ConfigParser.get_projected_atoms(model, project_operator.name))

    logger.debug(f"{len(projected_atoms)} projected atoms: {format_atoms(projected_atoms)}")
    logger.debug(LINE)

    return projected_atoms


def _destroy_atoms_if_term_selected(
    atom_term_pairs: list[dict[str, Symbol]], percent_or_number: DestructionSpec
) -> set[Symbol]:
    """
    Randomly select terms by given percentage (or number)
    and return all atoms corresponding to selected terms.

    :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
    :param percent_or_number: What percentage (or how many) terms are selected.
    :return: Destroyed atoms.
    """
    candidate_terms = set()
    for pair in atom_term_pairs:
        candidate_terms.add(pair["term"])

    destroyed_atoms = set()
    value = percent_or_number["value"]
    if percent_or_number["type"] == "p":
        num_selected_terms = round(len(candidate_terms) * value / 100)
    else:  # n, "auto" should not be present here
        num_selected_terms = min(len(candidate_terms), value)
    selected_terms = random.sample(sorted(candidate_terms), num_selected_terms)
    for pair in atom_term_pairs:
        if pair["term"] in selected_terms:
            destroyed_atoms.add(pair["atom"])

    return destroyed_atoms


# !todo subset of args selected


def _destroy_atoms_if_all_args_selected(
    atom_term_pairs: list[dict[str, Symbol]], percents_or_numbers: list[DestructionSpec]
) -> set[Symbol]:
    """
    Randomly select arguments based on the specified percentages (or numbers),
    and return all atoms whose terms have all their arguments selected.

    :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
    :param percents_or_numbers: What percentages (or how many) arguments are selected.
    :return: Destroyed atoms.
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
        else:  # n, "auto" should not be present here
            num_selected_args = min(len(candidate_args[i]), value)
        selected_args.append(random.sample(sorted(candidate_args[i]), num_selected_args))
    for pair in atom_term_pairs:
        if _is_tuple(pair["term"]) and len(pair["term"].arguments) == len(percents_or_numbers):
            all_args_selected = all(arg in selected_args[i] for i, arg in enumerate(pair["term"].arguments))
            if all_args_selected:
                destroyed_atoms.add(pair["atom"])

    return destroyed_atoms


def _destroy(
    model: Model,
    destroy_operators: list[DestroyOperator],
    projected_atoms: set[Symbol],
    logger: Logger,
) -> set[Symbol]:
    """
    Destroy a subset of atoms according to the runtime configuration.

    :param model: Model containing the atoms.
    :param destroy_operators: List of destroy operators.
    :param projected_atoms: Set of projected atoms
    :return: Set of prioritized atoms
    """
    destroyed_atoms: set[Symbol] = set()
    for destroy_operator in destroy_operators:
        atom_term_pairs = ConfigParser.get_atom_term_pairs(model, projected_atoms, destroy_operator.name)
        if len(destroy_operator) == 1:
            destroyed_atoms.update(_destroy_atoms_if_term_selected(atom_term_pairs, destroy_operator.get_first_spec()))
        else:
            destroyed_atoms.update(
                _destroy_atoms_if_all_args_selected(atom_term_pairs, destroy_operator.get_all_specs())
            )

    logger.debug(f"{len(destroyed_atoms)} destroyed atoms: {format_atoms(destroyed_atoms)}")
    logger.debug(LINE)

    prioritized_atoms = projected_atoms - destroyed_atoms

    logger.debug(f"{len(prioritized_atoms)} undestroyed atoms: {format_atoms(prioritized_atoms)}")
    logger.debug(LINE)

    return prioritized_atoms


def destroy_config(model: Model, config: ActiveConfig, logger: Logger) -> set[Symbol]:
    """
    Destroy portion of atoms as defined by LNS configuration.

    :param model: Model containing the atoms.
    :param config: Active configuration.
    :param logger: Logger instance.
    :return: Set of non destroyed atoms
    """
    projected = _project(model, config["project_operators"], logger)
    return _destroy(model, config["destroy_operators"], projected, logger)
