jaratoolbox
===========

Data analysis toolbox for JaraLab.

INSTALLATION
------------
These instructions assume you have Python 3.9 or newer and
[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/) installed
(this provides the `mkvirtualenv` and `workon` commands to work with Python virtual environments).

* Create and activate a virtual environment named `jaralab`:
  * `mkvirtualenv -p python3 jaralab`
  * (In later sessions, activate it with `workon jaralab`)
* Clone the repository (we generally place it in `~/src/`):
  * `cd ~/src/`
  * `git clone https://github.com/sjara/jaratoolbox.git`
  * `cd jaratoolbox`
* Install the package in development mode. This also installs the dependencies listed in `pyproject.toml`:
  * `pip install -e ./`
* Create a settings file:
  * `cp settings_EXAMPLE.py settings.py`
* Edit your `settings.py` file to define your data paths.
* Test the installation (with the `jaralab` environment active):
  * Run: `ipython --pylab`
  * Within ipython, run: `import jaratoolbox`
