
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

ini_parser () {
  INIFILE="$1"
  SECTION="$2"
  ITEM="$3"
  cat "$INIFILE" | sed -n /^\[$SECTION\]/,/^\[.*\]/p | grep "^[[:space:]]*$ITEM[[:space:]]*=" | sed s/.*=[[:space:]]*// | tr -d \\r
}

status_led () {
  if [ -f /usr/local/bin/status_led_$1 ] ; then
    sleep 0.2
    /usr/local/bin/status_led_$1
  fi
}

