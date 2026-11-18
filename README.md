# *fastlane*: A Framework for Answer Set Programming-based Large Neighborhood Search

The goal of this project is to implement an extensive and easily modifiable
implementation of LNS using the tools of [potassco](https://potassco.org/).

## Installation

The framework can be installed with any Python version newer than 3.12
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

## Documentation

The documentation can be accessed [here](https://docs.potassco.org/fastlane/)
or build and hosted using:

```bash
$ pip install .[doc]
$ zensical serve
```

## Usage

You can check a successful installation by running

```bash
$ fastlane -h
```
The [Getting started](https://docs.potassco.org/fastlane/getting_started/) section
provides information on how to use *fastlane*.

### Converter

The experimental `fastlane-convert` command can be used to convert an alaspo-style
JSON configuration into a *fastlane* configuration:

```bash
fastlane-convert input.json > out.lp
```

Conversion warnings are written to standard error. Use `fastlane-convert --help`
for command help.
