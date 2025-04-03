# Benchmark-tool

Collection of scripts and files used to run this framework with this [benchmark-tool](https://github.com/potassco/benchmark-tool).

## Usage

- Make sure mod_lns is correctly installed in a conda environment
- Clone the benchmark-tool repository
- Install lxml (`$ conda install lxml`)
- Copy files in this folder into the corresponding folders inside the benchmark-tool
- All following steps assume you are inside the benchmark-tool folder 
- Add the following line to `./src/benchmarktool/config.py`
```
from benchmarktool.resultparser.lns import lns
```
- Modify runscript-lns.xml for your use-case
- Set the conda environment where mod_lns is installed inside the `./program/mod_lns-conda` script
- Generate start script using:
```
$ ./bgen ./runscripts/runscript-lns.xml
```
- Start benchmarks using the start.py script generated 3 folders down inside the output folder
- Evaluate benchmarks using:
```
$ ./beval ./runscripts/runscript-lns.xml | ./bconv -m "time:t,cost" > results.ods
```
- The -m option accepts a comma-separated list of measures in the form `name[:{t,to,-}]` to be included in the table (optional argument determines coloring)
- All supported measures are defined in the resultparser
- For more information check the help pages of the different executables and the `./doc/README.md`