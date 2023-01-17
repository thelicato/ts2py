# ts2py

![](https://img.shields.io/pypi/v/ts2py)
![](https://img.shields.io/pypi/status/ts2py)
![](https://img.shields.io/pypi/pyversions/ts2py)
![](https://img.shields.io/pypi/l/ts2py)

Python-interoperability for Typescript-Interfaces.
Transpiles TypeScript-Interface-definitions to Python TypedDicts

## What is this
This repo is born as a fork of [ts2python](https://github.com/jecki/ts2python) written by Eckhart Arnold <arnold@badw.de>, Bavarian Academy of Sciences and Humanities. The reason behind this fork was that I needed a **simpler** way to quickly convert *TypeScript* interfaces to Python *TypedDict*. Once I started looking into the initial code I decided to change (and remove) a lot of stuff.
I also managed to split the code in multiple files and added [Typer](https://typer.tiangolo.com/) to create a beautiful CLI. The initial project should be much more powerful and should also have **support for run-time type-checking of JSON-data**.

## Purpose
Nowadays **a lot** of applications are created with TypeScript. To enable a much better way of developing when dealing with Python backend it could be useful to quickly convert [Typescript-Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html) into Python [TypedDicts](https://www.python.org/dev/peps/pep-0589/). In order to enable structural validation on the Python-side, ts2py transpiles the typescript-interface definitions to Python-data structure definitions.

## Installation

``ts2py`` can be installed from the command line with the command:
```
pip install ts2py
```

ts2py requires the parsing-expression-grammar-framework [DHParser](https://gitlab.lrz.de/badw-it/DHParser) which will automatically be installed as a dependency by the `pip`-command. ts2py requires at least Python Version 3.10 to run. However, the Python-code it produces is backwards compatible down to Python 3.6 thanks to the [typing extensions](https://pypi.org/project/typing-extensions/).

## Usage

In order to generate TypedDict-classes from Typescript-Interfaces, run `ts2py` on the Typescript-Interface definitions:
```
ts2py interfaces.ts
```
This generates a ``.py`` file in same directory as the source file that contains the TypedDict-classes and can simpy be imported in Python-Code:
```python
from interfaces import *
```

## License and Source Code

``ts2py`` is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

The complete source-code of ts2py can be downloaded from the [its git-repository](https://github.com/thelicato/ts2py).
