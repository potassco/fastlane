# Getting started

This framework can be used both as a command line tool and as a python module.
When using as a command line tool use the `-h` flag to see all available options:

```bash
mod_lns -h
```

The framework currently supports implementation of the clingo, clingo-dl and clingcon solvers,
and the approaches of LNS, ALNS, LNPS and ALNPS, selectable via different options and presets.

For finer control one can implement their own solver and/or strategy or modify existing ones through inheritance.

Any solver or other component should be implemented according to the interfaces described [here][interfaces] and
has to implement all abstract methods.
More details to the concrete implementation can be found in the corresponding [section][implementation].

When using the framework as a python module, the LNS object has to be initialized with the encoding files.
A dictionary of parameters can be passed during initialization of the `LNS` object, which intern is used
to overwrite attributes of the `LNSOptions` object. Alternatively, already initialized `LNSOptions` objects can also be provided.

The 'preset' parameter can be used to set multiple parameters at once according to predefined presets.
Manually set parameters will always override preset values. And preset values will overwrite default configuration values.
An example of the LNS initialization can be seen below or in [`./examples/demo.py`][test].
For a more detailed and step by step introduction to the framework, check out the [guide].

```python
from mod_lns.lns import LNS
from mod_lns.lns_options import LNS

options = LNSOptions(seed=42)
lns = LNS(
    ["./examples/golf.lp"],         # ASP encoding
    {                               # set additional parameters
        "time_limit": 60,           # overall time limit in seconds
    }
    options,                        # LNSOptions object containing defaults
)
```

The same search can be performed through the command line as follows:

```bash
mod_lns --seed=42 --time-limit=60 ./examples/golf.lp 
```

## Encodings

The encodings should contain some kind of optimization statement or soft constraint. The lns framework will work
with the solution cost derived by the solver.

When using `--destruction=declarative`, additional helper atoms must be specified. These include:
```
_project_op(ID,S).       % ID: identifier, S: signature 
_project(ID,A).          % ID: identifier, A: affected atom
_destroy_op(ID,V)        % ID: identifier, V: value i.e. percent/number/auto
_destroy(ID,A,S)         % ID: identifier, A: affected atom, S: selected term for destruction
_prioritize_op(ID,V,M)   % ID: identifier, V: value, M: modifier
_prioritize(ID,A).       % ID: identifier, A: affected atom
_config(ID,PID,DID,PIID) % ID: identifier, PID: project id, DID: destroy id, PIID: prioritize id
_strategy(ID,CID)        % ID: identifier, CID: config id
```
An example config encoding for the social golfer problem can be found in [`./examples/golf_config.lp`][golf_config].
A more complex example can be found in [`./examples/portfolio.lp`][portfolio].

## Benchmark-Tool

The [benchmark-tool] section provides some guidelines and examples on how to use this framework with
the [potassco-benchmark-tool].

[implementation]: ../implementation/index.md
[interfaces]: ../implementation/interfaces.md
[guide]: guide.md
[potassco-benchmark-tool]: https://potassco.org/benchmark-tool/
[demo]: examples/demo.md
[golf_config]: examples/golf_config.md
[portfolio]: examples/portfolio.md
[benchmark-tool]: benchmark-tool/index.md
