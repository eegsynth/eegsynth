# General installation instructions

The EEGsynth software is developed to be installed and started from the command-line terminal. This works smoothly on Linux and macOS (for those used to it), but it also works on Windows.

The first section consists of the installation of the dependencies, i.e. the external software that EEGsynth builds on.

## Using Anaconda

We recommend that you use [Anaconda](https://www.anaconda.com) to install Python. Please look in its installation instruction how to install it. Once you have installed conda, you should create a new environment, install some larger dependencies as binaries using `conda install`, and subsequently install EEGsynth using `pip install`.

```
conda create -y -n eegsynth python=3.12

conda activate eegsynth

conda install -y redis     # note that this is not yet sufficient for windows
conda install -y redis-py
conda install -y numpy
conda install -y scipy
conda install -y pyqt
conda install -y pyqtgraph
conda install -y python-levenshtein
conda install -y portaudio
conda install -y pyaudio
conda install -y -c conda-forge liblsl

pip install eegsynth
```

## Platform-specific instructions

- [Installation instructions for Linux](installation-linux.md)
- [Installation instructions for macOS](installation-macos.md)
- [Installation instructions for Windows](installation-windows.md)

After completing any specific dependencies for your operating system, you should return here and continue below.

## Install EEGsynth from github

```
git clone https://github.com/eegsynth/eegsynth.git
```

## Low-level test

Start Redis, buffer, and generatesignal.

Add the FieldTrip Python module to the PYTHONPATH, where `$EEGSYNTHPATH` is the EEGsynth base folder.

```
export PYTHONPATH=$PYTHONPATH:$EEGSYNTHPATH/src/lib
```

Then, in a Python console:

```
import FieldTrip

c = FieldTrip.Client()
c.connect(hostname='127.0.0.1')
h = c.getHeader()
print 'number of channels ' + str(h.nChannels)
```

Wait some time and then you can plot the EEG signals:

```
import matplotlib.pyplot as plt
import scipy

d = c.getData()
y = scipy.signal.detrend(d[-2500:,:])

plt.plot(y)
plt.title('Last 10 seconds in the FieldTrip buffer')
plt.show()
```
