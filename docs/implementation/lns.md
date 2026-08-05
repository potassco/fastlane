# LNS

This page gives an overview of the `LNS` class with all its methods.
If you want to modify the LNS adjusting these methods is the best start to do so.
Most LNS parameters are stored inside a `LNSOptions` instance. Default values can be accessed
via the provided presets.  

!!! note
    `UNSET` can used as a marker to differentiate between parameters that were not set and those
    that were explicitly set to `None`. Before starting the search, all remaining `UNSET` parameters
    will be set to `None`.
    Additional default parameters can be set using the `preset` argument/option.
    Use `fastlane -h` to see all available presets and their parameter values.

::: fastlane.lns.LNS

::: fastlane.lns_options.LNSOptions

## Helper classes

::: fastlane.Model

::: fastlane.Timer
