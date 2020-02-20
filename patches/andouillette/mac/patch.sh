#!/bin/bash

PATCHDIR=/Users/roboos/eegsynth/patches/andouillette

$PATCHDIR/terminal.scpt $PATCHDIR/buffer.sh
$PATCHDIR/terminal.scpt $PATCHDIR/redis.sh
$PATCHDIR/terminal.scpt $PATCHDIR/audio2ft.sh
$PATCHDIR/terminal.scpt $PATCHDIR/inputcontrol.sh
<<<<<<< HEAD:patches/andouillette/patch.sh
$PATCHDIR/terminal.scpt $PATCHDIR/playbacksignal.sh
=======
$PATCHDIR/terminal.scpt $PATCHDIR/lsl2ft.sh
# $PATCHDIR/terminal.scpt $PATCHDIR/playbacksignal.sh
>>>>>>> 71c0d3df8c6df126a86dc2ac9929dc17977a9f1c:patches/andouillette/mac/patch.sh

echo Waiting for a few seconds ...
sleep 10

<<<<<<< HEAD:patches/andouillette/patch.sh
#$PATCHDIR/terminal.scpt $PATCHDIR/lsl2ft.sh
=======
>>>>>>> 71c0d3df8c6df126a86dc2ac9929dc17977a9f1c:patches/andouillette/mac/patch.sh
$PATCHDIR/terminal.scpt $PATCHDIR/preprocessing.sh
$PATCHDIR/terminal.scpt $PATCHDIR/spectral.sh
$PATCHDIR/terminal.scpt $PATCHDIR/threshold.sh
$PATCHDIR/terminal.scpt $PATCHDIR/rms.sh

echo Waiting for a few seconds ...
sleep 5

$PATCHDIR/terminal.scpt $PATCHDIR/geomixer.sh
$PATCHDIR/terminal.scpt $PATCHDIR/quantizer.sh
$PATCHDIR/terminal.scpt $PATCHDIR/historycontrol.sh
# $PATCHDIR/terminal.scpt $PATCHDIR/historysignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/postprocessing.sh
$PATCHDIR/terminal.scpt $PATCHDIR/slewlimiter.sh

$PATCHDIR/terminal.scpt $PATCHDIR/outputmidi_avmixer.sh
$PATCHDIR/terminal.scpt $PATCHDIR/outputmidi_doepfer.sh

$PATCHDIR/terminal.scpt $PATCHDIR/plotcontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotsignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotspectral.sh
$PATCHDIR/terminal.scpt $PATCHDIR/vumeter.sh
