#!/bin/bash

curl -s http://www.example.com/perpi.html | bash

N=`ps aux | grep ngrok | wc -l`
if [ $N -lt 2 ] ; then
( /home/pi/bin/ngrok-tunnel.sh > /home/pi/bin/ngrok-tunnel.log ) &
fi

