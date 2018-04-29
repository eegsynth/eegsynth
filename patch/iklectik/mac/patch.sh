#!/bin/bash

PATCHDIR=`pwd`

$PATCHDIR/terminal.scpt $PATCHDIR/redis.sh
$PATCHDIR/terminal.scpt $PATCHDIR/buffer.sh
# $PATCHDIR/terminal.scpt $PATCHDIR/openbci2ft.sh
$PATCHDIR/terminal.scpt $PATCHDIR/outputartnet.sh
$PATCHDIR/terminal.scpt $PATCHDIR/launchcontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/spectral.sh
$PATCHDIR/terminal.scpt $PATCHDIR/postprocessing.sh
$PATCHDIR/terminal.scpt $PATCHDIR/historycontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotcontrol.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotsignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotspectral.sh
$PATCHDIR/terminal.scpt $PATCHDIR/outputcvgate.sh
