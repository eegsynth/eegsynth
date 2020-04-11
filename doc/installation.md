# General installation instructions

The EEGsynth software is developed to be executed from the command line terminal. This works smoothly on Linux and macOS (for those used to it), but it also works on Windows.

The first section consists of the installation of the dependencies, i.e. the external software that EEGsynth builds on.


## Using Anaconda

We recommend that you use [Anaconda](https://www.anaconda.com) to install Python. Please look in its installation instruction how to install it. Subsequently you should make a new environment, install some larger dependencies as binaries using `conda install`, and subsequently install EEGsynth using `pip install`.


```
conda create -n eegsynth python=3.7 anaconda
conda activate eegsynth

conda install redis
conda install redis-py
conda install numpy
conda install scipy
conda install pyqtgraph
conda install python-levenshtein
conda install portaudio
conda install pyaudio

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

## Install the binary dependencies on FieldTrip

For interfacing with the EEG amplifiers we use the FieldTrip buffer and the associated amplifier-specific applications. Each of them is a small executable that is implemented in C and already compiled. These executables are different for each computing platform (i386, ARM, etc.) and for each operating system. In the eegsynth/bin directory you can find a small installer script that helps you to select and download the correct ones.

On Linux and macOS you can use the following to install the buffer and the openbci2ft executables.

```
cd eegsynth/bin
install.sh
```

On Windows you have to download buffer.exe and openbci2ft.exe by hand from the [fieldtrip repository](https://github.com/fieldtrip/fieldtrip/tree/master/realtime/bin/win64) and copy them to the `bin` directory.

## Quick test

Start the buffer, redis, and openbci2ft.

Add the FieldTrip Python module to the PYTHONPATH, where \$EEGSYNTHPATH is the eegsynth base folder.

```
export PYTHONPATH=$PYTHONPATH:$EEGSYNTHPATH/lib
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
import scipy.signal

d = c.getData()
y = scipy.signal.detrend(d[-2500:,:])

plt.plot(y)
plt.title('Last 10 seconds in the FieldTrip buffer')
plt.show()
```
