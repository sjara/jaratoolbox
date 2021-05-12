jaratoolbox
===========

Data analysis toolbox for JaraLab

INSTALLATION (Ubuntu 20.04)
---------------------------
* Install dependencies and useful tools: 
  * `sudo apt-get install python3-numpy python3-h5py python3-matplotlib`
  * The following packages are not required, but recommended: `sudo apt-get python3-statsmodels python3-scipy ipython3`
* Clone the repository (we generally place it in ~/src/):
  * `cd ~/src/`
  * `git clone https://github.com/sjara/jaratoolbox.git`
  * `cd jaratoolbox`
* Create a settings file:
  * `cp settings_EXAMPLE.py settings.py`
* Modify your `settings.py` file to define your data paths.
* From `~/src/jaratoolbox` you can install the package (in development mode) with:
  * `pip3 install -e ./`
* Test the installation:
  * Run: `ipython3 --pylab`
  * Within ipython, run: `import jaratoolbox`
