"""See README for description."""
from distutils.core import setup
# import mpctools

setup(name="MPCTools",
    # dependencies
    install_requires=[
      "casadi==3.6.0",
      "numpy==1.23.5",
      ],
    version='2.4.2',
    description="Nonlinear MPC tools for use with CasADi",
    author="Michael Risbeck",
    author_email="risbeck@wisc.edu",
    url="https://bitbucket.org/rawlings-group/mpc-tools-casadi",
    long_description=__doc__,
    packages=["mpctools"],
    platforms=["N/A"],
    license="GNU LGPLv3",
)
