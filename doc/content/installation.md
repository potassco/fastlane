# Installation

mod_lns requires clingo 5.7, clingo-dl 1.5 and Python 3.10+. We recommend version 3.11.
An introduction to clingo can be found [here](https://potassco.org/doc/start/).

You can check a successful installation by running

```console
$ mod_lns -h
```

The project is hosted on [github](https://github.com/krr-up/large-neighbourhood-search) and should be installed from source.

```{warning}
This project is still in active development.
```

```{note}
The `setuptools` package is required to run the commands below.
We recommend the usage of a clean environment, e.g. using conda.
```

Execute the following commands in the top level mod_lns directory:

```console
$ git clone https://github.com/potassco/mod_lns
$ cd mod_lns
$ pip install .[full]
```
