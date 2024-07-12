"""
Strategy implementing LNS using hard constraints with lexicographic
optimization criteria and random declarative relaxation.
Based on HCLexiRND class.
"""

from typing import Any, Dict, List, Sequence, Tuple, Union

import clingo

from large_neighbourhood_search.lib.relaxation import relax_declarative
from large_neighbourhood_search.lib.strategies.hc_lexicographic_rnd import HCLexiRnd


class HCLexiDecl(HCLexiRnd):
    """
    LNS using hard constraints with lexicographic optimization criteria and random declarative relaxation.
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
