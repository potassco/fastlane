# Benchmark-tool

Collection of scripts and files used to run this framework with this [benchmark-tool](https://github.com/potassco/benchmark-tool).

## Usage

- Install the benchmark-tool (>v2.0.0)
- Copy files from the `benchmark-tool` folder to the corresponding folders inside the
  benchmark-tool directory structure
- Modify one of the provided runscripts to fit your use-case
- Make sure mod_lns is correctly installed in a conda environment
- For benchmarking on a cluster (dist jobs), set the correct environment inside
  `./templates/single.dist`
- Otherwise set the conda environment inside the `./programs/mod_lns-conda` script

- All following steps assume you are inside the benchmark-tool folder created by
  the benchmark-tool
- Generate a start script using:

```
bgen ./runscripts/runscript-dist-lns.xml
```

- Start the benchmarks by executing either the `start.sh` or `start.py` file found in
  the machine subfolder of the generated structure
- Evaluate the benchmarks using:

```
beval ./runscripts/runscript-dist-lns.xml | bconv -m "time:t,cost" -o results.ods
```

- The `-m` option accepts a comma-separated list of measures in the form
  `name[:{t,to,-}]` to be included in the table (optional argument determines coloring)
- All supported measures are defined in the resultparser
- For more information check the [benchmark-tool documentation](https://potassco.org/benchmark-tool/).
