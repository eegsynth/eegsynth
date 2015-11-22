# eegsynth-matlab
Converting real-time EEG into sounds and music.

This repository contains all code for http://www.eegsynth.org.

## Installation instructions for Raspbian

Use "raspi-config" to configure the correct keyboard, time-zone,
to extend the partition on the SD card and to disable the automatic
start of the graphical interface upon boot.

sudo apt-get update
sudo apt-get upgrade
sudo apt-get install screen
sudo apt-get install vim

### reconfigure the keyboard
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration

### install node.js
curl -sLS https://apt.adafruit.com/add | sudo bash
sudo apt-get install node

### install redis
sudo apt-get install redis-server
sudo pip install redis

### install EEGsynth from gitub
git clone https://github.com/robertoostenveld/eegsynth.git

### install MIDO to get MIDI working with Python
sudo pip install --upgrade pip
sudo pip install mido
sudo port selfupdate
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/opt/local/lib

sudo apt-get install libportmidi0
sudo apt-get install libportmidi-dev

Note: To use the Launch Control XL with the Raspberry Pi you must
first switch it to low power mode. To do this hold down both the
User and Factory Template buttons and insert the USB cable. Release
the Template buttons and press "Record Arm". Finally press the right
arrow button.

