# Installation instructions for Mac OS X

On Mac OS X there are multiple options for Python: you can either use the built-in version of python (which is /usr/bin/python) supplied by Apple, you can install Python (and most other dependencies) through the macports or homebrew package manager (see below), or you can use the Anaconda python distribution.

## Package managers

From [Wikipedia](https://en.wikipedia.org/wiki/Package_manager): *A package manager or package management system is a collection of software tools that automates the process of installing, upgrading, configuring, and removing computer programs for a computer's operating system in a consistent manner.*

For the general software dependencies (binaries and libraries) we are using either [HomeBrew](http://brew.sh) or [MacPorts](https://www.macports.org).

To make sure your package manager is up to date, you should do

```
brew update
```

or

```
sudo port selfupdate
```

To make sure you have wget, you should do

```
sudo port install wget
```

or

```
brew install wget
```

## Install MIDO for Python

MIDO is a MIDI package that is based on portaudio.

```
brew install portmidi
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib
```

## Redis

Install the Redis server and command-line client with brew :
```
brew install redis
```

If you want to connect between different computers, you then need to edit the configuration file:
```
sudo nano /etc/redis/redis.conf
```
and comment out the line "bind 127.0.0.1"

You can then, either:
- configure it to launch Redis when computer starts:
```
ln -sfv /usr/local/opt/redis/*.plist ~/Library/LaunchAgents
```
- launch it manually:
```
launchctl load ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
```
and then stop it later:
```
launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.redis.plist
```

## Install python modules

For the Python dependencies (packages) we are using pip. To install pip, you should do

```
sudo port install py27-pip
sudo port select --set pip pip27
sudo port select --set python python27
```

The graphical user interfaces of plotsignal and plotcontrol are generated using Qt4. This requires the bindings between Python and Qt to be installed with

```
sudo port install py27-pyside
```

To make sure the Python package manager is up to date, you should do
```
sudo pip install --upgrade pip
```

Subsequently you can install the Python modules
```
sudo pip install redis
sudo pip install mido
sudo pip install python-rtmidi
sudo pip install pyserial
sudo pip install pyosc
sudo pip install numpy
sudo pip install nilearn
sudo pip install sklearn
sudo pip install pyqtgraph
sudo pip install scipy
sudo pip install matplotlib
```

The plotting modules rely on PyQt4, which is a pain to install. It seems that on my mac011 with /opt/anaconda2/bin/python the following got it to work
```
brew tap cartr/qt4
brew tap-pin cartr/qt4
brew install cartr/qt4
brew install pyside
brew install cartr/qt4/pyqt
```
