# MPCTools: Nonlinear Model Predictive Control Tools for CasADi (Python Interface) #

Copyright (C) 2017

Michael J. Risbeck and James B. Rawlings.

MPCTools is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3, or (at your option) any later
version.

MPCTools is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the file
COPYING for more details.

## Availability ##

The latest development sources of MPCTools are also available via
anonymous access to a read-only Mercurial archive. There is also a web
interface to the archive available at
[Bitbucket](https://bitbucket.org/rawlings-group/mpc-tools-casadi)

## Installation ##

To use MPCTools, you will need a recent versions of

* Python 2.7 (see below for Python 3 support)
* Numpy
* Scipy
* Matplotlib
* Tkinter (only needed for `*_mpcsim.py` examples)
* CasADi (Version >=3.0; [download here](http://files.casadi.org))

With these packages installed, MPCTools can be downloaded from the
website above, and the mpctools folder can be manually placed in the user's
Python path, or the provided setup script `mpctoolssetup.py` can be used, e.g.,

    python mpctoolssetup.py install --user

to install for the current user only, or

    sudo python mpctoolssetup.py install

to install systemwide.

Code is used by importing `mpctools` within python scripts. See sample
files for complete examples.

### Python 3 Support ###

Support for Python 3.4+ has been added on an experimental basis. To use
MPCTools with Python 3, you will need to download the Python 3 zip from the
[Downloads](https://bitbucket.org/rawlings-group/mpc-tools-casadi/downloads])
section.

The Python 3 files are generated automatically from the Python 2 sources using
Python's `2to3` conversion utility. This translation seems to work, but there
may be subtle bugs. Please report any issues you discover.

## Documentation ##

Documentation for MPCTools is included in each function. We also
provide a cheatsheet (`doc/cheatsheet.pdf`). See sample files for complete
examples.

## Citing MPCTools ##

Because MPCTools is primarily an interface to CasADi, you should cite CasADi as
described on its [website](https://github.com/casadi/casadi/wiki/Publications).
In addition, you can cite MPCTools as

- Risbeck, M.J., Rawlings, J.B., 2015. MPCTools: Nonlinear model predictive
  control tools for CasADi (Python interface).
  `https://bitbucket.org/rawlings-group/mpc-tools-casadi`.

## Bugs ##

Questions, comments, bug reports can be posted on the
(issue tracker)(https://bitbucket.org/rawlings-group-mpc-tools-casadi/issues)
on Bitbucket.

Michael J. Risbeck  
<risbeck@wisc.edu>  
University of Wisconsin-Madison  
Department of Chemical Engineering
