# Getting started

## Installation

*fastlane* can be installed with any Python version newer than 3.12
using pip:

```bash
pip install potassco-fastlane
```

To access the latest updates and fixes you can either use:

```bash
pip install git+https://github.com/potassco/fastlane
```

Or alternatively build the tool yourself, which requires the `setuptools`
package. We recommend using conda, which includes `setuptools` in its default
Python installation. To build the tool manually run the following commands:

```bash
git clone https://github.com/potassco/fastlane
cd fastlane
conda create -n <env-name> python=3.14
conda activate <env-name>
pip install .
```

## Usage

This framework can be used both as a command line tool and as a python module.
When using as a command line tool use the `-h` flag to see all available options:

```bash
fastlane -h
```

*fastlane* currently supports implementation of the clingo, clingo-dl and clingcon solvers,
and the approaches of LNS, ALNS, LNPS and ALNPS, selectable via different options and presets.

For finer control one can implement their own solver and/or strategy or modify existing ones through inheritance.

Any solver or other component should be implemented according to the interfaces described [here][interfaces] and
has to implement all abstract methods.
More details to the concrete implementation can be found in the corresponding [section][implementation].

When using *fastlane* as a python module, the LNS object has to be initialized with the encoding files.
A dictionary of parameters can be passed during initialization of the `LNS` object, which intern is used
to overwrite attributes of the `LNSOptions` object. Alternatively, already initialized `LNSOptions` objects can also be provided.

The 'preset' parameter can be used to set multiple parameters at once according to predefined presets.
Manually set parameters will always override preset values. And preset values will overwrite default configuration values.
An example of the LNS initialization can be seen below or in [`./examples/demo.py`][test].
For a more detailed and step by step introduction to *fastlane*, check out the [guide].

```python
from fastlane.lns import LNS
from fastlane.lns_options import LNS

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
fastlane --seed=42 --time-limit=60 ./examples/golf.lp 
```

When no filenames are provided, the CLI reads piped or redirected standard input.
Use `-` to select standard input explicitly, including alongside named files:

```bash
cat file.lp | fastlane --preset=lns
fastlane --preset=lns < file.lp
cat file.lp | fastlane --preset=lns encoding.lp -
```

!!! note
    With no filenames and an interactive terminal, fastlane reports a missing-input error.
    Use `-` to read interactively instead.

## Encodings

The encodings should contain some kind of optimization statement or soft constraint. The lns framework will work
with the solution cost derived by the solver.

When using `--destruction=declarative`, additional helper atoms should be specified. These include:
```
_project_op(ID,S).           % ID: identifier, S: signature 
_project(ID,A).              % ID: identifier, A: affected atom
_destroy_op(ID,V)            % ID: identifier, V: value i.e. percent/number/auto
_destroy(ID,A,S)             % ID: identifier, A: affected atom, S: selected term for destruction
_prioritize_op(ID,V,M)       % ID: identifier, V: value, M: modifier
_prioritize(ID,A).           % ID: identifier, A: affected atom
_search_param(ID,(O,V))      % ID: identifier, O: option name, V: value
_config(ID,PID,DID,PIID,SID) % ID: identifier, PID: project id, DID: destroy id, PIID: prioritize id,
                             % SID: search operator id
_strategy(ID,CID)            % ID: identifier, CID: config id
```
An example config encoding for the social golfer problem can be found in [`./examples/golf_config.lp`][golf_config].

## Configuration converter

The `fastlane-convert` command is installed together with *fastlane* and runs
`fastlane.utils.config_converter` to convert *alaspo*[^1]-style JSON configurations
into fastlane configuration rules:

```console
fl-convert input.json > out.lp
```

Use `fastlane-convert --help` for command help.
Generated rules are written to standard output. Any warnings go to standard error.

Declarative relax/destroy operators accept nonnegative integer counts, fractions
between zero and one corresponding to whole percentages, or `"auto"`. Invalid
entries are skipped in full, while unsupported destroy types are ignored. 
`randomAtoms` rates are collected but are not yet supported.

For declarative operators, the first valid entry for each name is used. Later
entries with the same name are warned about and skipped, even if they specify a
different size kind.

Numeric sizes are pooled into a single rule per destroy operator.
For example, `"sizes": [0.1, 0.2, 0.3, 0.5]` for `weeks` generates

```
_destroy_sizes_0(10;20;30;50).
_destroy_op((weeks,N), p(N)) :- _destroy_sizes_0(N).
```

The generated `_config` rules reuse `_destroy_sizes_0(N)` in their bodies,
combined with the timeout domain when time limits are present. Helper predicates
are numbered separately for each numeric size domain. Automatic sizes retain
their constant destroy rule.

Nested search options are flattened. For compatibility, later search entries
inherit earlier parameters unless they override them. `timeouts` arrays generate
timeout-specific rules. Output order and duplicate handling are retained by the
converter.

!!! note
    The generated configuration is incomplete.
    `_destroy` rules and rules related to projection and prioritization are not included.
    Configurations and strategies are used differently between *alaspo* and *fastlane*.
    A more detailed description will be provided in the future.

## Benchmark-Tool

The [benchmark-tool] section provides some guidelines and examples on how to use this framework with
the [potassco-benchmark-tool].

[implementation]: ../implementation/index.md
[interfaces]: ../implementation/interfaces.md
[guide]: guide.md
[potassco-benchmark-tool]: https://potassco.org/benchmark-tool/
[demo]: examples/demo.md
[golf_config]: examples/golf_config.md
[benchmark-tool]: benchmark-tool/index.md
[^1]: Eiter, T., Geibinger, T., Higuera, N., Musliu, N., Oetsch, J., Stepanova, D.:
ALASPO: An adaptive large-neighbourhood ASP optimiser.
In: Proceedings of the Nineteenth International Conference on Principles of Knowledge Representation and Reasoning (KR 2022), pp. 565--569. (2022)
