# supergrader

![supergrader badge](https://badge.fury.io/py/supergrader.png)

![travis badge](https://travis-ci.org/michaelpb/supergrader.png?branch=master)

Configurable automatic grading system for web programming and Computer Science
classes, also useful for automating checks of directories of programming
assignments.

**NOTE:** Very unfinished, still a WIP.


## Installation

Assuming Python's `pip` is installed (for Debian-based systems, this can be
installed with `sudo apt-get install python-pip`), supergrader can be installed
directly from PyPI:

```
pip install supergrader
```

Python versions 3.3+ (and 2.6+) are supported and tested against.

## Full usage

```
usage: supergrader [-h] [-v] [directories [directories ...]]

Automatic grading system.

positional arguments:
  directories           one or more packages

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
```

# Contributing

New features, tests, and bug fixes are welcome.
