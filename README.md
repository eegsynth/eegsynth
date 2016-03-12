# EEGsynth

Converting real-time EEG into sounds, music and visual effects. This repository contains all code for http://www.eegsynth.org.

## General instructions

### install EEGsynth from gitub
```
git clone https://github.com/eegsynth/eegsynth.git
```

There are some dependencies from FieldTrip, which you can download and install using

```
cd eegsynth/bin
install.sh
```

## Installation instructions for Raspbian

Use "raspi-config" to configure the correct keyboard, time-zone, to extend the partition on the SD card and to disable the automatic start of the graphical interface upon boot.
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install screen
sudo apt-get install vim
```

### Reconfigure the keyboard

The default keyboard layout is UK-English, which is probably not what you have.

```
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration
```

### Install node.js

This is used for the web interface.

```
curl -sLS https://apt.adafruit.com/add | sudo bash
sudo apt-get install node
```

### Install redis

This is used for inter-process communication between  modules.

```
sudo apt-get install redis-server
sudo easy_install pip
sudo pip install redis
```

The redis command line interface is an useful tool for monitoring and debugging the redis server:
```
redis-cli monitoring
```

### Switch to low-power mode

To use the Launch Control XL connected directly (without powered USB hub) with the Raspberry Pi you must first switch it to low-power mode. To do this hold down both the *User* and *Factory Template* buttons and insert the USB cable. Release the buttons and press *Record Arm*. Finally press the right arrow button.

### Fix audio problems on Raspberry Pi

The following are some attempts to get the synthesizer module working nicely with the crappy audio interface of the Raspberry Pi.

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

## Installation instructions for OS-X

### Install MIDO for Python

MIDO is a MIDI package that is based on portaudio.

```
sudo pip install --upgrade pip
sudo pip install mido
sudo port selfupdate
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/opt/local/lib
```

```
sudo apt-get install libportmidi0
sudo apt-get install libportmidi-dev
```

### Install audio for Python

```
sudo apt-get install python-pyaudio python3-pyaudio
```

```
sudo apt-get install alsa-utils
sudo apt-get install mpg321
sudo apt-get install lame
```

### Misc

```
sudo pip install pyserial
```

