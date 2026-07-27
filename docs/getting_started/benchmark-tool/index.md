# Benchmark-Tool

This section gives a brief overview on how to use the LNS framework
with the [poatssco-benchmark-tool].

## Usage

- Install the benchmark-tool and create the benchmarking environment using:

```
pip install potassco-benchmark-tool
btool init
```

- Copy the [`mod_lns-conda`][prgm] program into the `programs` folder.
- Install [runlim] into the `programs` folder
- Make sure all programs are executable.
- Modify one of the provided [runscripts] to fit your use-case and copy it into the `runscripts` folder.
- Make sure mod_lns is correctly installed in a conda environment
- Depending on your system, you might need to load your conda environment during benchmark runs
    - For benchmarking on a cluster (dist jobs), load the environment inside `./templates/single.dist`
    - Otherwise set the conda environment inside the `./programs/mod_lns-conda` script

- Generate a start script using:

```
btool gen ./runscripts/runscript-dist-lns.xml
```

- Start the benchmarks by executing either the `start.sh` or `start.py` file found in the
  machine subfolder of the generated structure
- Evaluate the benchmarks using:

```
btool eval ./runscripts/runscript-dist-lns.xml | btool conv -m "time:t,optimum" -o results.xlsx
```

- The `-m` option accepts a comma-separated list of measures in the form `name[:{t,to,-}]` to be included
  in the table (optional argument determines coloring)
- For more information check the benchmark-tool [documentation].

[potassco-benchmark-tool]: https://potassco.org/benchmark-tool/
[documentation]: https://docs.potassco.org/benchmark-tool/
[prgm]: program.md
[runscripts]: runscripts.md
[runlim]: https://github.com/arminbiere/runlim