#!/bin/bash

PATCHDIR=`pwd`
TERMINAL=$PATCHDIR/terminal.scpt

$TERMINAL $PATCHDIR/redis.sh
$TERMINAL $PATCHDIR/buffer.sh

sleep 3 # give the previous section some time to start

$TERMINAL $PATCHDIR/launchcontrol.sh
$TERMINAL $PATCHDIR/playbacksignal.sh
#$TERMINAL $PATCHDIR/generatesignal.sh
#$TERMINAL $PATCHDIR/openbci2ft.sh
$TERMINAL $PATCHDIR/preprocessing.sh

$TERMINAL $PATCHDIR/spectral.sh
$TERMINAL $PATCHDIR/historycontrol.sh
$TERMINAL $PATCHDIR/postprocessing.sh

# for visual feedback to the EEG operator
$TERMINAL $PATCHDIR/plotsignal.sh
$TERMINAL $PATCHDIR/plotspectral.sh
$TERMINAL $PATCHDIR/plotcontrol.sh

# for the analog synthesizer mixing
$TERMINAL $PATCHDIR/outputcvgate.sh

# for the video mixing
$TERMINAL $PATCHDIR/geomixer.sh
$TERMINAL $PATCHDIR/outputmidi.sh

# for the feedback on the time in the performance
$TERMINAL $PATCHDIR/generatecontrol.sh
$TERMINAL $PATCHDIR/outputartnet.sh

