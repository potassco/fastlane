"""
Strategy implementing LNS using hard constraints with weighted sum as optimization criteria and random relaxation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple, Union

import clingo

from mod_lns.lib.relaxation import relax_declarative
from mod_lns.lib.strategies.classic_weighted_sum_rnd import ClassicWeightedSumRnd


# pylint: disable=duplicate-code
class ClassicWeightedSumDecl(ClassicWeightedSumRnd):
    """
    classic LNS with weighted sum as optimization criteria and declarative relaxation.
    """

    def relax(
        self,
        model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
        relax_parameters: Dict[str, Any],
    ) -> List[Tuple[clingo.symbol.Symbol, bool]]:
        """
        Relax portion of atoms given by the relax_parameters.
        Use declarative random relaxation.

        :param model: Dictionary containing list of shown and true atoms.
        :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
        :param relax_parameters: Parameters used to determine relaxed atoms.
        :type relax_parameters: Dict[str, Any]
        :return: Fixed (not relaxed) atoms.
        :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
        """
        return relax_declarative(model, relax_parameters)
