# Software installation instructions

The EEGsynth software is developed with Linux and OS X in mind. In principle it should also work on Windows, but we don't actively work on that platform.

For Linux we are specifically targetting [Raspbian](http://www.raspbian.org), which is a free Debian-based operating system optimized for the [Raspberry Pi](https://www.raspberrypi.org) hardware. This allows to build a dedicated EEGsynth on the low-cost Raspberry Pi platform.

## General instructions that apply to all systems

### Install EEGsynth from gitub
```
git clone https://github.com/eegsynth/eegsynth.git
```

### Install the dependencies on FieldTrip

For interfacing with the EEG amplifiers we use the FieldTrip buffer and the associated amplifier-specific applications. Each of them is a small executable that is implemented in C and already compiled. These executables are different for each computing platform (i386, ARM, etc.) and for each operating system. In the eegsynth/bin directory you can find a small installer script that helps you to select and download the correct ones.

```
cd eegsynth/bin
install.sh
```

### Switch the Launch Control XL to low-power mode

To use the Launch Control XL connected directly (without powered USB hub) with the Raspberry Pi you must first switch it to low-power mode. To do this hold down both the *User* and *Factory Template* buttons and insert the USB cable. Release the buttons and press *Record Arm*. Finally press the right arrow button.

## Installation instructions for Raspbian

Use "raspi-config" to configure the correct keyboard, time-zone, to extend the partition on the SD card and to disable the automatic start of the graphical interface upon boot.
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install screen
sudo apt-get install vim
sudo apt-get install git
```

### Reconfigure the keyboard

The default keyboard layout is UK-English, which is probably not what you have.
```
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration
```

## Installation instructions for Linux

### Package managers

From [Wikipedia](https://en.wikipedia.org/wiki/Package_manager): *A package manager or package management system is a collection of software tools that automates the process of installing, upgrading, configuring, and removing computer programs for a computer's operating system in a consistent manner.*

The general package manager on Linux depends on the distribution you are using. Debian-based distributions (such as Ubuntu, Raspbian, Mint, etc.) use dpkg and apt-get. Redhat-based systems (such as CentOS, Fedora) use rpm and yum.

For installing Python packages there are  [easy_install](https://setuptools.readthedocs.io/en/latest/easy_install.html) and [pip](https://pip.pypa.io/en/stable/).

In the subsequent Linux installation instructions we assume apt-get and pip as the primary package managers.

### Install the web interface

EEGsynth includes a web interface that allows you to start and stop modules and to edit the patch configuration. The installation of this is detailed in the [README](../interface/README.md) document for the interface.

### Install redis

This is used for inter-process communication between modules.

```
sudo apt-get install redis-server
```

Redis is automatically started on Raspberry Pi. If you look for running processes, you should see
```
pi@hackpi:/etc/redis $ ps aux | grep redis
redis      434  0.4  2.0  29332  2436 ?        Ssl  10:40   0:14 /usr/bin/redis-server 127.0.0.1:6379       
```

If you want to connect between different computers, you should edit /etc/redis/redis.conf and specify that it should bind to all network interfaces rather than only 127.0.0.1 (default). Edit the configuration"
```
sudo nano /etc/redis/redis.conf
```

and comment out the line "bind 127.0.0.1" like this:
```
# By default Redis listens for connections from all the network interfaces
# available on the server. It is possible to listen to just one or multiple
# interfaces using the "bind" configuration directive, followed by one or
# more IP addresses.
#
# Examples:
#
# bind 192.168.1.100 10.0.0.1
# bind 127.0.0.1                  ## COMMENTED OUT FOR EEGSYNTH
```

After changing the configuration file, you can kill the server, which will then restart with the correct configuration:
```
pi@raspberry:/etc/redis $ ps aux | grep redis
sudo kill -9 <ID>
```

And you should see that it restarts and binds to all interfaces:
```
pi@raspberry:/etc/redis $ ps aux | grep redis
redis     2840  0.0  2.2  29332  2684 ?        Ssl  11:35   0:00 /usr/bin/redis-server *:6379               
```

The redis command line interface is an useful tool for monitoring and debugging the redis server:
```
redis-cli monitor
```

### Install portmidi

This is used for MIDI communication.
```
sudo apt-get install libportmidi-dev
```

### Install python modules

For Python packages we are using pip as the package manager. To install pip, use the following
```
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
sudo easy_install pip
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

### Install audio

This is only needed for the software synthesizer module, which runs fine on OS X but which still has issues on the Raspberry Pi.

```
sudo apt-get install python-pyaudio
sudo apt-get install jackd
```

The following might actually not be needed.

```
sudo apt-get install alsa-utils
sudo apt-get install mpg321
sudo apt-get install lame
```

### Fix audio problems on Raspberry Pi

The following are some attempts to get the software synthesizer module working nicely with the audio interface of the Raspberry Pi.

See https://dbader.org/blog/crackle-free-audio-on-the-raspberry-pi-with-mpd-and-pulseaudio

```
sudo apt-get install pulseaudio
sudo apt-get install mpd
sudo apt-get install mpc
```

This did not solve it, I uninstalled them again.

```
sudo apt-get install libasound2-dev
sudo apt-get install python-dev
wget https://pypi.python.org/packages/source/p/pyalsaaudio/pyalsaaudio-0.8.2.tar.gz
tar xvzf pyalsaaudio-0.8.2.tar.gz
cd pyalsaaudio-0.8.2
python setup.py build
sudo python setup.py install
```

## Installation instructions for OS X

### Package managers

For general software (binaries and libraries) we are using either [HomeBrew](http://brew.sh) or  [MacPorts](https://www.macports.org).

When using MacPorts: to make sure it is up to date, you should do

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

For Python packages we are using pip as the package manager. To make sure it is up to date, you should do
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

## Quick test

Start the EEGsynth modules: buffer, redis, and openbci2ft

Add the FieldTrip python module to the PYTHONPATH, where $EEGSYNTHPATH is the eegsynth base folder.
```
export PYTHONPATH=$PYTHONPATH:$EEGSYNTHPATH/lib
```

Then, in a python console:
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
