#! /bin/sh

PATH=/opt/anaconda2/bin:/sbin:/bin:/usr/bin

DIR=`dirname "$0"`
NAME=`basename "$0" .sh`

# helper files are stored in the directory containing this script
PIDFILE="$DIR"/"$NAME".pid
LOGFILE="$DIR"/"$NAME".log
INIFILE="$DIR"/"$NAME".ini
COMMAND="$DIR"/"$NAME".py

log_action_msg () {
  echo $* 1>&1
}

log_action_err () {
  echo $* 1>&2
}

check_running_process () {
  if [ ! -f "$PIDFILE" ]; then
    return 1
  else
    kill -0 `cat "$PIDFILE"` 2> /dev/null
    return $?
  fi
}

do_start () {
  log_action_msg "Starting $NAME"
  check_running_process && log_action_err "Error: $NAME is already started" && exit 1
  # start the process in the background
  ( "$COMMAND" > "$LOGFILE" ) &
  echo $! > "$PIDFILE"
}

do_stop () {
  log_action_msg "Stopping $NAME"
  check_running_process || log_action_err "Error: $NAME is already stopped"
  check_running_process || exit 1
  kill -9 `cat "$PIDFILE"`
  rm "$PIDFILE"
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
