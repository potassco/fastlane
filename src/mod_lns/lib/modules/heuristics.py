from typing import Any


def generate_heuristic_subprogram(lns_config: dict[str, Any]) -> str:
    """
    Generate #heuristic statements for LNPS and integrity constraints for LNS
    from predicate signatures of projected atoms.

    :param lns_config: LNS configuration dictionary.
    :type lns_config: dict[str, Any]
    :return: #heuristic statements and integrity constraints.
    :rtype: str
    """
    heuristic_subprogram = ""
    # TODO maybe signatures into lns dict
    for signature in set().union(*lns_config["project_operators"].values()):
        name = signature[0]
        args = ",".join(["X" + str(i) for i in range(signature[1])])
        atom = f"{name}({args})"
        heuristic_subprogram += (
            f"#heuristic {atom} : __heuristic({atom},W,M,t), W != inf. [W,M]"
            f":- not {atom}, __heuristic({atom},inf,true,t)."
            f":- {atom}, __heuristic({atom},inf,false,t)."
        )
    return heuristic_subprogram
