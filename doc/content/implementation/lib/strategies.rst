.. _ref_strat:

.. currentmodule:: mod_lns.interfaces.strategy

Implementations of :class:`StrategyInterface`
==============================================

.. currentmodule:: mod_lns.lns_config

Shown below is a default strategy implementation and a strategy using heuristics and a prioritized
search called heulingo. Both strategies use their own configuration class.

.. note::

    Heulingo is based on the heulingo clingo application developed by Irumi Sugimori
    (`Large Neighborhood Prioritized Search for Combinatorial Optimization with
    Answer Set Programming <https://doi.org/10.24963/kr.2024/72>`_).

Default strategy
-----------------

.. automodule:: mod_lns.lib.strategies.default_strategy
    :members:

Heulingo
--------------

.. automodule:: mod_lns.lib.strategies.heulingo
    :members:
