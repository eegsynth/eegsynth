# Installation instructions for Linux

For Linux we are specifically targetting [Raspbian](http://www.raspbian.org), which is a free Debian-based operating system optimized for the [Raspberry Pi](https://www.raspberrypi.org) hardware. This allows to build a dedicated EEGsynth on the low-cost Raspberry Pi platform.

## Installation instructions for Raspbian

Use "raspi-config" to configure the correct keyboard, time-zone, to extend the partition on the SD card and to disable the automatic start of the graphical interface upon boot.
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install screen
sudo apt-get install vim
sudo apt-get install git
```

### Reconfigure the Raspberry Pi keyboard layout  

The default keyboard layout is UK-English, which is probably not what you have.
```
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration
```

## Generic installation instructions for Linux

### Package managers

From [Wikipedia](https://en.wikipedia.org/wiki/Package_manager): *A package manager or package management system is a collection of software tools that automates the process of installing, upgrading, configuring, and removing computer programs for a computer's operating system in a consistent manner.*

The general package manager on Linux depends on the distribution you are using. Debian-based distributions (such as Ubuntu, Raspbian, Mint, etc.) use dpkg and apt-get. Redhat-based systems (such as CentOS, Fedora) use rpm and yum.

For installing Python packages there are  [easy_install](https://setuptools.readthedocs.io/en/latest/easy_install.html) and [pip](https://pip.pypa.io/en/stable/).

In the subsequent Linux installation instructions we assume apt-get and pip as the primary package managers.

### Install Redis

This is used for inter-process communication between modules.

```
sudo apt-get install Redis-server
```

Redis will be automatically started on Linux. If you look for running processes, you should see
```
pi@hackpi:/etc/Redis $ ps aux | grep Redis
Redis      434  0.4  2.0  29332  2436 ?        Ssl  10:40   0:14 /usr/bin/Redis-server 127.0.0.1:6379       
```

If you want to connect between different computers, you should edit /etc/Redis/Redis.conf and specify that it should bind to all network interfaces rather than only 127.0.0.1 (default). Edit the configuration"
```
sudo nano /etc/Redis/Redis.conf
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
pi@raspberry:/etc/Redis $ ps aux | grep Redis
sudo kill -9 <ID>
```

And you should see that it restarts and binds to all interfaces:
```
pi@raspberry:/etc/Redis $ ps aux | grep Redis
Redis     2840  0.0  2.2  29332  2684 ?        Ssl  11:35   0:00 /usr/bin/Redis-server *:6379               
```

The Redis command line interface is an useful tool for monitoring and debugging the Redis server:
```
Redis-cli monitor
```

### Install portmidi

This is used for MIDI communication.
```
sudo apt-get install libportmidi-dev
```

### Install dependencies for rtmidi

This is required for the python-rtmidi package further down
```
sudo apt-get install libasound2-dev
sudo apt-get install libjack-dev
```

### Install python modules

For Python packages we are using pip as the package manager. To install pip, use the following
```
sudo apt-get install python-pip
```

To make sure it is up to date, you should do
```
sudo pip install --upgrade pip
```

Subsequently you can install the Python modules
```
sudo pip install Redis
sudo pip install mido
sudo pip install python-rtmidi --pre
sudo pip install pyserial
sudo pip install pyosc
sudo pip install numpy
sudo pip install nilearn
sudo pip install sklearn
sudo pip install bitalino
```

Due to the large number of non-Python dependencies, installing the scipy package is easier with apt-get than with pip.

```
sudo apt-get install python-scipy
```

### Install graphics 

The plotsignal and plotcontrol modules are using pyqtgraph, which uses Qt4. This can be installed with

```
sudo apt-get install python-pyqtgraph
```

### Install audio

This is only needed for the software synthesizer module. Note that good quality and smooth audio output on the Raspberry Pi requires an external audio card.

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

