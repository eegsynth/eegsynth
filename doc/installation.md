# Installation instructions

The EEGsynth software is developed with Linux and macOS in mind. In principle it should also work on Windows, but we don't actively work on that platform.

The first section consists of the installation of the dependencies, i.e. the external software that EEGsynth builds on.

  * [Installation instructions for Linux](installation-linux.md)
  * [Installation instructions for macOS](installation-macos.md)
  * [Installation instructions for Windows](installation-windows.md)

After completing the external dependencies for your operating system, you should return here and continue below.

## Install EEGsynth from github

```
git clone https://github.com/eegsynth/eegsynth.git
```

## Install the binary dependencies on FieldTrip

For interfacing with the EEG amplifiers we use the FieldTrip buffer and the associated amplifier-specific applications. Each of them is a small executable that is implemented in C and already compiled. These executables are different for each computing platform (i386, ARM, etc.) and for each operating system. In the eegsynth/bin directory you can find a small installer script that helps you to select and download the correct ones.

```
cd eegsynth/bin
install.sh
```

## Switch the Launch Control XL to low-power mode

To use the Launch Control XL connected directly (without powered USB hub) with the Raspberry Pi you must first switch it to low-power mode. To do this hold down both the *User* and *Factory Template* buttons and insert the USB cable. Release the buttons and press *Record Arm*. Finally press the right arrow button.


## Quick test

Start the EEGsynth modules: buffer, Redis, and openbci2ft

Add the FieldTrip Python module to the PYTHONPATH, where $EEGSYNTHPATH is the eegsynth base folder.
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
