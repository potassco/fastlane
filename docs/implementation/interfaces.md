# Interfaces

This page describes the interfaces provided to customize the LNS search.
All interfaces can be found in the `mod_lns.interfaces` module.
Example implementations of these interfaces can be found in the `lib` submodule.


## Adaptive Strategy Interface

This interface gives guidelines on how to implement adaptive strategies for adaptive LNS.

::: mod_lns.interfaces.adaptive_strategy.AdaptiveStrategy


## Auto Destruction Converter

All custom auto destruction converters (for determining relax rates automatically) should
respect the this interface.

::: mod_lns.interfaces.auto_destruction_converter.AutoDestructionConverter

## Solver Interface

Solver implementations should follow the `Solver` Interface and make use of the `SolverConfig` class.

::: mod_lns.interfaces.solver.Solver
