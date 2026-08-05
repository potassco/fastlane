# Interfaces

This page describes the interfaces provided to customize the LNS search.
All interfaces can be found in the `fastlane.interfaces` module.
Example implementations of these interfaces can be found in the `lib` submodule.


## Adaptive Strategy Interface

This interface gives guidelines on how to implement adaptive strategies for adaptive LNS.

::: fastlane.interfaces.adaptive_strategy.AdaptiveStrategy


## Auto Destruction Converter

All custom auto destruction converters (for determining destruction rates automatically) should
respect the this interface.

::: fastlane.interfaces.auto_destruction_converter.AutoDestructionConverter

## Solver Interface

Solver implementations should follow the `Solver` Interface and make use of the `SolverConfig` class.

::: fastlane.interfaces.solver.Solver
