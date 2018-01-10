EEGsynth web interface
======================

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

Having started the web interface, you can connect on another computer, smart phone or tablet with the address http://RASPBERRY_PI_ADDRESS:3000.

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
