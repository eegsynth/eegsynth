#!/bin/bash

MODULE=`basename $0 .sh`

EEGSYNTH=$HOME/eegsynth
INIDIR=`dirname $0`

# $EEGSYNTH/module/$MODULE/$MODULE.sh -i $INIDIR/$MODULE.ini

# the redis.conf contains details on the bind address, writing the database to disk, etc.

if [ `which redis-server` == /opt/local/bin/redis-server ]
then 
  CONFIG=/opt/local/etc/redis.conf
else
  CONFIG=""
fi

echo starting \"redis-server $CONFIG\"
redis-server $CONFIG
