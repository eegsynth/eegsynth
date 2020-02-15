# Installation instructions for Windows

Since we don't have a Windows setup to develop and test it on, we cannot provide detailed installation instructions. We recommend that you use [Anaconda](https://www.anaconda.com) to install Python. Please look in the Linux and/or macOS installation instruction for the dependencies that you need to install.

## Using Anaconda

When using [Anaconda](https://www.anaconda.com), this is more or less how to get started with the installation.

```
conda create -n eegsynth python=3.7 anaconda
conda activate eegsynth

conda install -c binstar redis-server # see https://anaconda.org/binstar/redis-server
conda install redis-py
conda install numpy
conda install scipy
conda install pyqtgraph
conda install python-levenshtein

pip install configparser
pip install mido
pip install python-rtmidi
pip install pyserial
pip install python-osc # for Python >= 3.6
pip install OSC        # for Python <= 3.5
pip install matplotlib
pip install bitalino
pip install fuzzywuzzy[speedup]
pip install nilearn
pip install sklearn
pip install neurokit
pip install paho-mqtt
```
