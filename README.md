jaratoolbox
===========

Data analysis toolbox for JaraLab

INSTALLATION (Ubuntu 14.04)
---------------------------
* Install dependencies and useful tools: 
  * `sudo apt-get install python-numpy python-h5py python-matplotlib python-scipy ipython`
* Clone the repository:
  * `git clone https://github.com/sjara/jaratoolbox.git`
  * `cd jaratoolbox`
* Prepare settings:
  * `cp settings_EXAMPLE.py settings.py`
* Modify your `settings.py` file to define your data paths.
* Add the toolbox to the Python path. For example, if your folder is `~/src/jaratoolbox/`, add the following line to the file `~/.bashrc`:
  * `export PYTHONPATH=$PYTHONPATH:~/src`
* Test the installation:
  * Re-login or open a new terminal (to make sure the Python path is updated).
  * Run: `ipython --pylab`
  * Within iPython, run: `import jaratoolbox`
