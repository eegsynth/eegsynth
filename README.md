# eegsynth-matlab
Converting real-time EEG into sounds and music.

This repository contains all code for http://www.eegsynth.org.

## Installation instructions for Raspbian

### reconfigure the keyboard
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration

### install node.js
curl -sLS https://apt.adafruit.com/add | sudo bash
sudo apt-get install node

### install redis
sudo apt-get install redis-server

### install EEGsynth from gitub
git clone https://github.com/robertoostenveld/eegsynth.git
