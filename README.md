# large_neighbourhood_search

The goal of this project is to implement an extensive and easily modifiable implementation of LNS using the tools of [potassco](https://potassco.org/).
A detailed documentation can be build in `./doc` as described in `./doc/README.md`, after a successful installation described below.

## Installation

The `setuptools` package is required to run the commands below.
We recommend the usage of conda, which already includes `setuptools` in its default python installation.

```bash
$ git clone https://github.com/potassco/large_neighbourhood_search
$ cd large_neighbourhood_search
$ conda create -n <env-name> python=3.11
$ conda activate <env-name>
$ pip install .[full]
```

## Usage

You can check a successful installation by running

```bash
mod_lns -h
```

An example for the usage of the framework can be found in `./examples/demo.py`
