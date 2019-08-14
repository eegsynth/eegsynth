#!/bin/bash

PATCHDIR="eegsynth/patches/biochill"
#PATCHDIR="pwd"
TERMINAL="lxterminal -e"

$TERMINAL $PATCHDIR/redis.sh
$TERMINAL $PATCHDIR/buffer.sh

sleep 3 # give the previous section some time to start

$TERMINAL $PATCHDIR/bitalino2ft.sh
$TERMINAL $PATCHDIR/heartrate.sh
$TERMINAL $PATCHDIR/plotsignal.sh
$TERMINAL $PATCHDIR/plotcontrol.sh

sleep 3 # give the previous section some time to start

$TERMINAL $PATCHDIR/recordsignal.sh
$TERMINAL $PATCHDIR/recordcontrol.sh
$TERMINAL $PATCHDIR/recordtrigger.sh
$TERMINAL $PATCHDIR/outputartnet.sh




