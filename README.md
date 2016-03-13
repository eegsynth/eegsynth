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
sudo apt-get install git
```

### Reconfigure the keyboard

The default keyboard layout is UK-English, which is probably not what you have.

```
sudo dpkg-reconfigure console-data
sudo dpkg-reconfigure keyboard-configuration
```

### Install the web interface

EEGsynth includes a web interface that allows you to start and stop modules and to edit the patch configuration. The web interface is implemented with node.js and would normally be started by a standard user (not root) on port 3000. Since it is more convenient to have it running on port 80, the instructions below include an explanation of port forwarding using iptables.

Please note that the web interface is not required, you can also start/stop/edit all modules with a terminal and text editor (if you have a screen and keyboard attached) or from the command line (if you ssh into the Raspberry Pi).

#### Install node.js

This is used for the web interface. Start with the (outdated) version that is included in raspbian, then upgrade to a later version using nvm. The advantage of npm (node package manager) and nvm (node version manager) is that they install all required files locally and don't interfere with the system installation or with the installation of other users.

```
sudo apt-get install nodejs
sudo apt-get install npm

wget -qO- https://raw.githubusercontent.com/creationix/nvm/v0.31.0/install.sh | bash

nvm install v4.2.6
```

The following should show the correct version

```
node -v
```

####  Start the web interface

```
cd eegsynth/interface
npm install
node index.js
```

Having started the web interface, you can connect on another computer, smart phone or tablet with the address http://<RASPBERRY_PI_ADDRESS>:3000.

To facilitate development of the web interface, it is useful to run it with [supervisor](https://github.com/petruisfan/node-supervisor), which will automatically restart if changes to the code are detected.

```
sudo npm install node-supervisor -g

cd eegsynth/interface
supervisor index.js
```

To ensure that the web interface keeps running for prolonged amounts of time, it is useful to run it with [forever](https://github.com/foreverjs/forever), which will automatically restart the interface if it crashes due to some unexpected reason.

```
sudo npm install forever -g

cd eegsynth/interface
forever start index.js
```

####  Redirect from port 80 to 3000

The firewall can be used to redirect incoming traffic from the usual port 80 to the actual port 3000 where the web interface is running. You start by installing the iptables firewall:

```
sudo apt-get update
sudo apt-get install iptables iptables-persistent
sudo /etc/init.d/iptables start
```

Subsequently you add the rule to forward incoming connections on port 80 to port 3000 and save it so that it is persistent over reboots.

```
sudo iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 3000
sudo iptables -t nat -L
sudo iptables -t nat -S

sudo sh -c 'iptables-save > /etc/iptables/rules.v4 '
```

####  Automatically start the web interface after every reboot

To start the web interface following every reboot, you can create a script $HOME/bin/startup.sh like this

```
#!/bin/bash

# this is needed to install the nvm application
. $HOME/.nvm/nvm.sh
nvm use v4.2.6

cd $HOME/eegsynth/interface
/usr/local/bin/forever start index.js
```

If you then add the following line added to your crontab, it will automatically start the web interface at every reboot and keep it running forever.

```
@reboot $HOME/bin/startup.sh > $HOME/bin/startup.log 2>&1
```

You may also want to consider using [duckdns](https://www.duckdns.org) or [ngrok](https://ngrok.com) to facilitate the management of the IP address.

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


If you want to connect between different computers, you should edit /etc/redis/redis.conf and specify that it should bind to all network interfaces rather than only 127.0.0.1 (default). Edit the configuration

```
nano /etc/redis/redis.conf
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

And you should see that it binds to all interfaces:

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

```
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
sudo easy_install pip

sudo pip install redis
sudo pip install mido
sudo pip install pyserial
sudo pip install pyosc
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

### Switch the Launch Control XL to low-power mode

To use the Launch Control XL connected directly (without powered USB hub) with the Raspberry Pi you must first switch it to low-power mode. To do this hold down both the *User* and *Factory Template* buttons and insert the USB cable. Release the buttons and press *Record Arm*. Finally press the right arrow button.



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

## Misc

```
hg clone ssh://hg@bitbucket.org/robertoostenveld/python-edf
sudo python setup.py install
```

