#!/bin/bash

PATH=/opt/anaconda2/bin:/sbin:/bin:/usr/bin:/usr/local/bin

# include library with helper functions
. "$(dirname "$0")/../../lib/EEGsynth.sh"

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`
BINDIR=$DIR/../../bin

# helper files are stored in the directory containing this script
PIDFILE="$DIR"/"$NAME".pid
LOGFILE="$DIR"/"$NAME".log
INIFILE="$DIR"/"$NAME".ini
COMMAND="$BINDIR/parallel"
shini_parse $INIFILE
OPTIONS="$BINDIR/buffer "$ini_fieldtrip_port

killtree() {
    local pid=$1 child
    for child in $(pgrep -P $pid); do
        killtree $child
    done
     [ $pid -ne $$ ] && kill -kill $pid 2> /dev/null
}

do_start () {
  status_led red
  log_action_msg "Starting $NAME"
  check_running_process && log_action_err "Error: $NAME is already started" && exit 1
  # start the process in the background
  date > "$LOGFILE"
  ( exec "$COMMAND" $OPTIONS >> "$LOGFILE" ) &
  echo $! > "$PIDFILE"
  status_led green
}

do_stop () {
  status_led red
  status_led red
  log_action_msg "Stopping $NAME"
  check_running_process || log_action_err "Error: $NAME is already stopped"
  check_running_process || exit 1
  killtree `cat "$PIDFILE"`
  rm "$PIDFILE"
  status_led green
}

do_status () {
  check_running_process && YESNO=" " || YESNO=" not "
  log_action_msg "$NAME is${YESNO}running"
}

case "$1" in
  start)
        do_start
        ;;
  restart)
        check_running_process && do_stop
        do_start
        ;;
  stop)
        do_stop
        ;;
  status)
        do_status
        ;;
  *)
        echo "Usage: $0 start|stop|restart|status" >&2
        exit 3
        ;;
esac
