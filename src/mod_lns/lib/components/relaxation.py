"""
Different relaxation methods for LNS.
"""

import random
from logging import Logger  # nocoverage
from typing import Any

import clingo
from clingo.symbol import Function, Symbol, SymbolType

from mod_lns import Model
from mod_lns.lib.utils import format_atoms
from mod_lns.parser.config_parser import ConfigParser

LINE = "-" * 50


def relax_declarative(
    model: Model,
    relax_rate: int,
) -> set[Symbol]:
    """
    Relax portion of selected atoms given by the relax_rate.
    ASP encoding has to contain `_lns_select/1` and `_lns_fix/2` predicates.

    :param model: model.
    :type model: Model
    :param relax_rate: Percentage of atoms to relax.
    :type relax_rate: int
    :return: Fixed (not relaxed) atoms.
    :rtype: set[Symbol]
    """
    fixed_atoms: set[Symbol] = set()
    selected_atoms: set[Symbol] = set()
    declared_fixed_atoms: dict[clingo.symbol.Symbol, set[Symbol]] = {}
    # !inefficient
    for atom in model.true:
        # get possible selection
        if atom.match("_lns_select", 1):
            if atom.arguments[0] not in selected_atoms:
                selected_atoms.add(atom.arguments[0])
                declared_fixed_atoms[atom.arguments[0]] = set()
        # associate selecttion with fixed atoms
        elif atom.match("_lns_fix", 2):
            if atom.arguments[1] in declared_fixed_atoms:
                declared_fixed_atoms[atom.arguments[1]].add(atom.arguments[0])
    # sample selection atoms
    if len(selected_atoms) == 1:
        symbols = selected_atoms.copy()
    else:
        symbols = random.sample(
            selected_atoms,
            round(len(selected_atoms) * (1 - relax_rate / 100)),
        )
    # fix corresponding atoms
    for s in symbols:
        fixed_atoms.update(declared_fixed_atoms[s])
    return fixed_atoms


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


def _project(model: Model, config: dict, logger: Logger) -> set[Symbol]:
    """
    Project atoms based on the configuration.

    :return: Set of projected atoms
    :rtype: set[Symbol]
    """
    projected_atoms = set()

    for project_operator in config["project_operators"]:
        projected_atoms.update(ConfigParser.get_projected_atoms(model, config["op_specs"], project_operator["name"]))

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
    :param percent_or_number: What percentage (or how many) terms are selected by.
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


# TODO subset of args selected
def _destroy_atoms_if_all_args_selected(
    atom_term_pairs: list[dict[str, Symbol]], percents_or_numbers: list[dict[str, Any]]
) -> set[Symbol]:
    """
    Randomly select arguments by given percentages (or numbers)
    and return all atoms corresponding to terms whose all arguments are selected.

    :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
    :type atom_term_pairs: list[dict[str, Symbol]]
    :param percents_or_numbers: What percentages (or how many) arguments are selected by.
    :type percents_or_numbers: list[dict[str, Any]]
    :return: Destroyed atoms.
    :rtype: set[Symbol]
    """

    def _is_tuple(self, term: Symbol) -> bool:
        return term.type == SymbolType.Function and not term.name

    candidate_args = [set() for i in range(len(percents_or_numbers))]
    selected_args = []

    for pair in atom_term_pairs:
        if _is_tuple(pair["term"]) and len(pair["term"].arguments) == len(percents_or_numbers):
            for i, arg in enumerate(pair["term"].arguments):
                candidate_args[i].add(arg)

    destroyed_atoms = set()
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


def _destroy(config: dict, projected_atoms: set[Symbol], logger: Logger) -> set[Symbol]:
    """
    Destroy a subset of atoms according to the configuration.

    :param model: Model containing the atoms.
    :type model: Model
    :param projected_atoms: Set of projected atoms
    :type projected_atoms: set[Symbol]
    :return: Set of prioritized atoms
    :rtype: set[Symbol]
    """
    destroyed_atoms: set[Symbol] = set()
    for destroy_operator in config["destroy_operators"]:
        atom_term_pairs = ConfigParser.get_atom_term_pairs(
            config["op_specs"], projected_atoms, destroy_operator["name"]
        )
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


def relax_config(model: Model, config: dict, logger: Logger) -> set[Symbol]:
    """
    Relax portion of atoms as defined by LNS configuration.

    :param config: LNS configuration dictionary.
    :type config: dict
    :return: Set of heuristic atoms
    :rtype: set[Symbol]
    """
    projected = _project(model, config, logger)
    return _destroy(config, projected, logger)
