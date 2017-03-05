# Installation instructions for Mac OS-X

## Installation instructions for OS X

### Package managers

From [Wikipedia](https://en.wikipedia.org/wiki/Package_manager): *A package manager or package management system is a collection of software tools that automates the process of installing, upgrading, configuring, and removing computer programs for a computer's operating system in a consistent manner.*

For the general software dependencies (binaries and libraries) we are using either [HomeBrew](http://brew.sh) or  [MacPorts](https://www.macports.org). To make sure MacPorts is up to date, you should do

```
sudo port selfupdate
```

### Install MIDO for Python

MIDO is a MIDI package that is based on portaudio.

```
brew install portmidi
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib
```

### Redis

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

### Install python modules

For the Python dependencies (packages) we are using pip. To install pip for the default OS-X Python version 2.7, you should do

```
sudo port install py27-pip
sudo port select --set pip pip27
```

To make sure it is up to date, you should do
```
sudo pip install --upgrade pip
```

Subsequently you can install the Python modules
```
sudo pip install redis
sudo pip install mido
sudo pip install pyserial
sudo pip install pyosc
sudo pip install numpy
sudo pip install nilearn
sudo pip install sklearn
```
