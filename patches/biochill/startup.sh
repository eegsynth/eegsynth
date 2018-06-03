#!/bin/bash

PATCHDIR=`pwd`

$PATCHDIR/terminal.scpt $PATCHDIR/redis.sh
$PATCHDIR/terminal.scpt $PATCHDIR/buffer.sh
$PATCHDIR/terminal.scpt $PATCHDIR/bitalino2ft.sh
$PATCHDIR/terminal.scpt $PATCHDIR/plotsignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/recordsignal.sh
$PATCHDIR/terminal.scpt $PATCHDIR/heartrate.sh
