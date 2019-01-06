# Installation instructions for Mac macOS

On Mac macOS there are multiple options for Python: you can either use the built-in version of python (which is /usr/bin/python) supplied by Apple, you can install Python (and most other dependencies) through the macports or homebrew package manager (see below), or you can use the Anaconda python distribution.

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
brew install wget
```

or

```
sudo port install wget
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
brew install Redis
```

If you want to connect between different computers, you then need to edit the configuration file:
```
sudo nano /etc/Redis/Redis.conf
```
and comment out the line "bind 127.0.0.1"

You can then, either:
- configure it to launch Redis when computer starts:
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

## Install python modules

For the Python dependencies (packages) we are using pip. If you have installed brew, you will probably have pip already. You can check like this

```
which pip
```

If it returns /usr/local/bin/pip, it is the version of pip (and python) that comes with brew.

To install pip using macports, you should do

```
sudo port install py27-pip
sudo port select --set pip pip27
sudo port select --set python python27
```

If you are using brew, all software (including Python) is installed using your own permissions. When using macports, it is installed as root user and you will have to add sudo prior to the subsequent commands.

To make sure the Python package manager is up to date, you should do
```
pip install --upgrade pip
```

or when using macports
```
sudo pip install --upgrade pip
```


Subsequently you can install the Python modules
```
pip install Redis
pip install mido
pip install python-rtmidi
pip install pyserial
pip install pyosc
pip install numpy
pip install nilearn
pip install sklearn
pip install pyqtgraph
pip install scipy
pip install matplotlib
```

The graphical user interfaces of plotsignal and plotcontrol are generated using Qt4. This requires the bindings between Python and Qt to be installed using brew as follows
```
brew tap cartr/qt4
brew tap-pin cartr/qt4
brew install cartr/qt4/pyqt
```

or using macports as follows
```
sudo port install py27-pyside
```
