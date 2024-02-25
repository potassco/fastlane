# Installation

large_neighbourhood_search requires clingo 5.7 and Python 3.8+. We recommend version 3.10.
An introduction to clingo can be found [here](https://potassco.org/doc/start/).

You can check a successful installation by running

```console
$ large_neighbourhood_search -h
```

## Installing with pip


The python large_neighbourhood_search package can be found [here](https://pypi.org/project/large_neighbourhood_search/).

```console
$ pip install large_neighbourhood_search
```

## Development

### Installing from source

The project is hosted on [github](https://github.com/potassco/large_neighbourhood_search) and can
also be installed from source.

```{warning}
We recommend this only for development purposes.
```

```{note}
The `setuptools` package is required to run the commands below.
```

Execute the following command in the top level large_neighbourhood_search directory:

```console
$ git clone https://github.com/potassco/large_neighbourhood_search
$ cd large_neighbourhood_search
$ pip install -e .[all]
```
