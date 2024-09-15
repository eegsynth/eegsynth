# Installation instructions for Linux

NOTE: the general installation instructions using Anaconda should cover most of the installation, the notes below are older notes and probably not needed any more.

## Raspberry Pi

For the Raspberry Pi we are specifically targetting [Raspbian](http://www.raspbian.org), which is a free Debian-based operating system optimized for the [Raspberry Pi](https://www.raspberrypi.org) hardware. This allows to build a dedicated EEGsynth on the low-cost Raspberry Pi platform.

## Installation instructions for Raspbian

Use "raspi-config" to configure the correct keyboard, timezone, to extend the partition on the SD card and to disable the automatic start of the graphical interface upon boot.

```
sudo apt update
sudo apt upgrade
sudo apt install screen
sudo apt install vim
sudo apt install git
```

### Reconfigure the Raspberry Pi keyboard layout

The default keyboard layout is UK-English, which is probably not what you have.

```
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration
```

## Generic installation instructions for Linux

### Package managers

From [Wikipedia](https://en.wikipedia.org/wiki/Package_manager): _A package manager or package management system is a collection of software tools that automates the process of installing, upgrading, configuring, and removing computer programs for a computer's operating system in a consistent manner._

The general package manager on Linux depends on the distribution you are using. Debian-based distributions (such as Ubuntu, Raspbian, Mint, etc.) use dpkg and apt. Redhat-based systems (such as CentOS, Fedora) use rpm and yum.

For installing Python packages there are [easy_install](https://setuptools.readthedocs.io/en/latest/easy_install.html) and [pip](https://pip.pypa.io/en/stable/).

In the subsequent Linux installation instructions we assume apt and pip as the primary package managers.

### Install Redis

This is used for inter-process communication between modules.

```
sudo apt install redis-server
```

Redis will be automatically started on Linux. If you look for running processes, you should see

```
pi@hackpi:~ $ ps aux | grep redis
redis      434  0.4  2.0  29332  2436 ?        Ssl  10:40   0:14 /usr/bin/redis-server 127.0.0.1:6379
```

If you want to connect between different computers, you should edit `/etc/redis/redis.conf` and specify that it should bind to all network interfaces rather than only the (default) internal 127.0.0.1 address. Edit the configuration with

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
pi@raspberry:~ $ ps aux | grep redis
sudo kill -9 <ID>
```

And you should see that it restarts and binds to all interfaces:

```
pi@raspberry:~ $ ps aux | grep redis
Redis     2840  0.0  2.2  29332  2684 ?        Ssl  11:35   0:00 /usr/bin/redis-server *:6379
```

The Redis command line interface is an useful tool for monitoring and debugging the Redis server:

```
redis-cli monitor
```

### Install portmidi

This is used for MIDI communication.

```
sudo apt install libportmidi-dev
```

### Install dependencies for rtmidi

This is required for the python-rtmidi package further down

```
sudo apt install libasound2-dev
sudo apt install libjack-dev
```

### Install Python modules

For Python we are using pip as the package manager. You can use either conda or virtualenv to create a virtual environment.

```
conda create -n eegsynth python==3.12
conda activate eegsynth
```

or

```
python3 -m venv eegsynth-env 
source eegsynth-env/bin/activate
```

Subsequently you can install EEGsynth and its dependencies with `pip install eegsynth`. A number of dependencies can be installed one-by-one using

```
pip install bitalino
pip install mido
pip install sklearn
pip install pyOSC          # for Python <= 3.4
pip install python-osc     # for Python >= 3.5
pip install python-rtmidi  # for Python >= 3.5
pip install wiringpi       # only for Raspberry Pi
```

Due to the large number of non-Python dependencies, installing the scipy package is easier with `apt` or with `conda` than with pip.

```
sudo apt install python-scipy
```

### Install graphics

The graphical user interfaces of `plotsignal`, `plotcontrol`, `plotspectral` and `plottrigger` are implemented with pyqtgraph, which uses either PyQt6, PyQt5 or PySide. This can be installed with

```
sudo apt install python-pyqtgraph
sudo apt install python3-pyqt5 # for Python 3
```

### Install audio

This is only needed for the software synthesizer module. Note that good quality and smooth audio output on the Raspberry Pi requires an external audio card.

```
sudo apt install python-pyaudio
sudo apt install jackd
```
