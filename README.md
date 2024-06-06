# large_neighbourhood_search

The goal of this project is to implement a extensive and easily modifiable implementation of LNS using the tools of [potassco](https://potassco.org/).
A detailed documentation can be build in `./doc` using `make html`.

## Installation

The `setuptools` package is required to run the commands below.
We recommend the usage of conda, which already includes `setuptools` in its default python installation.

```bash
$ git clone https://github.com/potassco/large_neighbourhood_search
$ cd large_neighbourhood_search
$ conda create -n <env-name> python=3.11
$ conda activate <env-name>
$ pip install -e .[full]
```

## Usage

You can check a successful installation by running

```bash
large_neighbourhood_search -h
```

An example usage of the framework can be found in `./examples/demo.py`

## Development

To improve code quality, we use [nox] to run linters, type checkers, unit
tests, documentation and more. We recommend installing nox using [pipx] to have
it available globally.git 

```bash
# install
python -m pip install pipx
python -m pipx install nox

# run all sessions
nox

# list all sessions
nox -l

# run individual session
nox -s session_name

# run individual session (reuse install)
nox -Rs session_name
```

Note that the nox sessions create [editable] installs. In case there are issues,
try recreating environments by dropping the `-R` option. If your project is
incompatible with editable installs, adjust the `noxfile.py` to disable them.

We also provide a [pre-commit][pre] config to autoformat code upon commits. It
can be set up using the following commands:

```bash
python -m pipx install pre-commit
pre-commit install
```

[nox]: https://nox.thea.codes/en/stable/index.html
[pipx]: https://pypa.github.io/pipx/
[pre]: https://pre-commit.com/
[editable]: https://setuptools.pypa.io/en/latest/userguide/development_mode.html
