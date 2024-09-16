# Installation instructions for macOS

NOTE: the general installation instructions using Anaconda should cover most of the installation, the notes below might be outdated and are probably not needed any more.

## Python

On Mac macOS there are multiple options for Python: you can either use the built-in version of Python (which is /usr/bin/python) supplied by Apple, you can install Python (and most other dependencies) through the _MacPorts_ or _HomeBrew_ package manager (see below), or you can use the _Anaconda_ Python distribution.

## Package managers

From [Wikipedia](https://en.wikipedia.org/wiki/Package_manager): _A package manager or package management system is a collection of software tools that automates the process of installing, upgrading, configuring, and removing computer programs for a computer's operating system in a consistent manner._

For the general software dependencies (binaries and libraries) we are using [HomeBrew](http://brew.sh). To make sure your package manager is up to date, you should do:

```
brew update
```

To make sure you have wget, you should do

```
brew install wget
```

## Install MIDO for Python

MIDO is a MIDI package that is based on portaudio.

```
brew install portmidi
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib
```

## Install liblsl

The pylsl module requires the dynamic library `liblsl.dylib` to be installed. For some binary wheels it is installed along with `pip install pylsl` in the `pylsl/lib` directory. Alternatively, it can be installed with

```
conda install -c conda-forge liblsl
```

or specifically on macOS with

```
brew install lsl
```

## Give the terminal access to the microphone

In order for `audio2ft` and `demodulatetone` to receive audio on macOS Monterey, you have to give the terminal access to the microphone. Go to System Preferences, Security and Privacy, Microphone, and enable Terminal.

## Redis

Install the Redis server and command-line client:

```
brew install redis
```

If you want to connect between different computers, you then need to edit the configuration file:

```
sudo nano /usr/local/etc/redis.conf
```

and comment out the line "bind 127.0.0.1"

You can then, either:

- configure it to launch Redis when your computer starts:

```
ln -sfv /usr/local/opt/Redis/*.plist ~/Library/LaunchAgents
```

- launch it manually:

```
launchctl load ~/Library/LaunchAgents/homebrew.mxcl.Redis.plist
```

and then stop it later:

```
launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.Redis.plist
```

## Install Python modules

For the Python dependencies (packages) we are using pip. If you have installed brew, you will probably have pip already. You can check like this

```
which pip
```

If it returns /usr/local/bin/pip, it is the version of pip (and Python) that comes with brew.

To make sure the Python package manager is up to date, you should do

```
pip install --upgrade pip
```

Subsequently you can install EEGsynth and its dependencies with `pip install eegsynth`. A number of dependencies can be installed one-by-one using

```
pip install bitalino
pip install mido
pip install sklearn
pip install pyOSC           # for Python <= 3.4
pip install python-osc      # for Python >= 3.5
pip install python-rtmidi   # for Python >= 3.5
```

The graphical user interfaces of `plotsignal`, `plotcontrol`, `plotspectral` and `plottrigger` are implemented with pyqtgraph, which uses either PyQt5, PyQt6 or PySide.

When using Anaconda, the bindings between Python and Qt can be installed as follows:

```
conda install pyqt
conda install pyqtgraph
```

When using brew and Python2, the bindings between Python and Qt can be installed as follows:

```
brew tap cartr/qt4
brew install qt@4
```
