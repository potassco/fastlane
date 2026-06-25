"""
Components for implementing fixation via heuristics in the context of LNS.
"""

from clingo.symbol import Function, Number, Symbol

from mod_lns.parser.config_parser import ConfigParser
from mod_lns.utils.types import ActiveConfig, ConfigCatalog


def generate_heuristic_subprogram(config_catalog: ConfigCatalog) -> str:
    """
    Generate #heuristic statements for LNPS and integrity constraints for LNS
    from predicate signatures of projected atoms.

    :param config_catalog: LNS configuration catalog.
    :type config_catalog: ConfigCatalog
    :return: #heuristic statements and integrity constraints.
    :rtype: str
    """
    heuristic_subprogram = ""
    for signature in set().union(*config_catalog["project_operators"].values()):
        name = signature[0]
        args = ",".join(["X" + str(i) for i in range(signature[1])])
        atom = f"{name}({args})"
        heuristic_subprogram += (
            f"#heuristic {atom} : __heuristic({atom},W,M,t), W != inf. [W,M]"
            f":- not {atom}, __heuristic({atom},inf,true,t)."
            f":- {atom}, __heuristic({atom},inf,false,t)."
        )
    return heuristic_subprogram


def get_fixed_atoms_heuristics(
    active_config: ActiveConfig, spec_ops: dict[str, set[Symbol]], fixed_atoms: set[Symbol], step: int
) -> set[Symbol]:
    """
    Get fixed atoms according to heuristics.

    :param active_config: LNS configuration dictionary.
    :type active_config: ActiveConfig
    :param spec_ops: Dictionary of operator specifications.
    :type spec_ops: dict[str, set[Symbol]]
    :param fixed_atoms: Set of fixed atoms from previous iteration.
    :type fixed_atoms: set[Symbol]
    :param step: Current LNS iteration.
    :type step: int
    :return: Set of fixed atoms for current iteration.
    :rtype: set[Symbol]
    """
    prioritized_atoms: set[Symbol] = set()
    heu_atoms: set[Symbol] = set()

    for prioritize_operator in active_config["prioritize_operators"]:
        targets = ConfigParser.get_heuristic_targets(spec_ops, fixed_atoms, prioritize_operator["name"])
        for target in targets:
            prioritized_atoms.add(target)
            if prioritize_operator["value"] == "inf":
                value = Function("inf")
            else:
                value = Number(prioritize_operator["value"])
            heu_atoms.add(
                Function("__heuristic", [target, value, Function(prioritize_operator["modifier"]), Number(step)])
            )

    # without prioritize specification
    for atom in fixed_atoms - prioritized_atoms:
        heu_atoms.add(Function("__heuristic", [atom, Number(1), Function("true"), Number(step)]))

    return heu_atoms
