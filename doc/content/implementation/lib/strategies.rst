.. _ref_strat:

.. currentmodule:: large_neighbourhood_search.interfaces.strategy

Implementations of :class:`StrategyInterface`
==============================================

Listed below are multiple strategy implementations, which describe different combinations
of the following approaches:

| **Classic vs. Hard constrained search:**
| While during a classic search the cost of solutions are compared after they are calculated, in the hard constrained mode, a constraint enforcing a better solution is added to the grounding.

| **Weighted sum vs. Lexicographic optimization**
| Whether weighted sum or a lexicographic ordering is used to calculate the cost of a solution.

| **Random vs. Declarative random relaxation**
| While with random relaxation a part of all true atoms is relaxed, with declarative random relaxation the group of atoms, from which the random selection is made, can be specified. 


.. note::
    When using lexicographic optimization priorities have to be consecutive, e.g. only priorities 1 and 3 are not supported.

ClassicWeightedSumRnd
----------------------

.. currentmodule:: large_neighbourhood_search.interfaces.strategy

This class is a direct implementation of :class:`StrategyInterface`.

.. automodule:: large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd
    :members:

ClassicLexiRnd
---------------

.. currentmodule:: large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd

This class inherits from :class:`ClassicWeightedSumRnd` and overwrites some methods as described below.

.. automodule:: large_neighbourhood_search.lib.strategies.classic_lexicographic_rnd
    :members:

ClassicLexiDecl
---------------

.. currentmodule:: large_neighbourhood_search.lib.strategies.classic_lexicographic_rnd

This class inherits from :class:`ClassicLexiRnd` and overwrites some methods as described below.

.. automodule:: large_neighbourhood_search.lib.strategies.classic_lexicographic_declarative
    :members:

HCWeightedSumRnd
----------------------

.. currentmodule:: large_neighbourhood_search.interfaces.strategy

This class is a direct implementation of :class:`StrategyInterface`.

.. automodule:: large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd
    :members:

HCLexiRnd
---------------

.. currentmodule:: large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd

This class inherits from :class:`HCWeightedSumRnd` and overwrites some methods as described below.

.. automodule:: large_neighbourhood_search.lib.strategies.hc_lexicographic_rnd
    :members:

HCLexiDecl
---------------

.. currentmodule:: large_neighbourhood_search.lib.strategies.hc_lexicographic_rnd

This class inherits from :class:`HCLexiRnd` and overwrites some methods as described below.

.. automodule:: large_neighbourhood_search.lib.strategies.hc_lexicographic_declarative
    :members:
