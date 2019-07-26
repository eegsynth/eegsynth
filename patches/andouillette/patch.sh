#!/bin/bash

PATCHDIR=/Users/roboos/eegsynth/patches/andouillette

$PATCHDIR/terminal.scpt $PATCHDIR/buffer.sh
$PATCHDIR/terminal.scpt $PATCHDIR/redis.sh

$PATCHDIR/terminal.scpt $PATCHDIR/audio2ft.sh

echo Waiting for a few seconds ...
sleep 3

#$PATCHDIR/terminal.scpt $PATCHDIR/lsl2ft.sh
#$PATCHDIR/terminal.scpt $PATCHDIR/preprocessing.sh
$PATCHDIR/terminal.scpt $PATCHDIR/playbacksignal.sh

$PATCHDIR/terminal.scpt $PATCHDIR/spectral.sh

$PATCHDIR/terminal.scpt $PATCHDIR/threshold.sh
$PATCHDIR/terminal.scpt $PATCHDIR/rms.sh

$PATCHDIR/terminal.scpt $PATCHDIR/historycontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/historysignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/postprocessing.sh
$PATCHDIR/terminal.scpt $PATCHDIR/slewlimiter.sh

$PATCHDIR/terminal.scpt $PATCHDIR/outputmidi.sh

$PATCHDIR/terminal.scpt $PATCHDIR/inputcontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotcontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotsignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotspectral.sh
$PATCHDIR/terminal.scpt $PATCHDIR/vumeter.sh
