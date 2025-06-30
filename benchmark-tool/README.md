# Benchmark-tool

Collection of scripts and files used to run this framework with this [benchmark-tool](https://github.com/potassco/benchmark-tool).

## Usage

- Make sure mod_lns is correctly installed in a conda environment
- Clone the benchmark-tool repository (>v2.0.0) and install the module
- Copy files in this folder into the corresponding folders inside the benchmark-tool
- Modify runscript-lns.xml for your use-case
- Set the conda environment where mod_lns is installed inside the `./program/mod_lns-conda` script
- For benchmarking on a cluster you also have to set the correct environment inside `./templates/single.dist`

- All following steps assume you are inside the benchmark-tool folder
- Generate start script using:
```
$ bgen ./runscripts/runscript-lns.xml
```
- Start benchmarks using the start.py script generated 3 folders down inside the output folder
- Evaluate benchmarks using:
```
$ beval ./runscripts/runscript-lns.xml | bconv -m "time:t,cost" -o results.ods
```
- The -m option accepts a comma-separated list of measures in the form `name[:{t,to,-}]` to be included in the table (optional argument determines coloring)
- All supported measures are defined in the resultparser
- For more information check the benchmark-tool documentation [here](https://potassco.org/benchmark-tool/).
