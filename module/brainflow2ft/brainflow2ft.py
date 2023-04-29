#!/usr/bin/env python

# Brainflow2ft reads data from an EEG device and writes it to a FieldTrip buffer
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2022 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import os
import sys
import time

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations

if hasattr(sys, "frozen"):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == "__main__" and sys.argv[0] != "":
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == "__main__":
    path = os.path.abspath("")
    file = os.path.split(path)[-1] + ".py"
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, "../../lib"))
import EEGsynth
import FieldTrip

def _setup():
    """Initialize the module
    This adds a set of global variables
    """
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, debug=patch.getint("general", "debug", default=1))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _start():
    """Start the module
    This uses the global variables from setup and adds a set of global variables
    """
    global patch, name, path, monitor
    global ft_host, ft_port, ft_output, delay, board_id, streamer_params, params, board

    try:
        ft_host = patch.getstring("fieldtrip", "hostname")
        ft_port = patch.getint("fieldtrip", "port")
        monitor.success("Trying to connect to buffer on %s:%i ..." % (ft_host, ft_port))
        ft_output = FieldTrip.Client()
        ft_output.connect(ft_host, ft_port)
        monitor.success("Connected to output FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to output FieldTrip buffer")

    # get the general options from the configuration file
    delay = patch.getfloat("general", "delay")

    # get the options that are specific for BrainFlow
    board_id             = patch.getint("brainflow", "board_id", default=-1)
    streamer_params      = patch.getstring("brainflow", "streamer_params", default=None)
    params               = BrainFlowInputParams()
    params.ip_port       = patch.getint("brainflow", "ip_port", default=0)
    params.serial_port   = patch.getstring("brainflow", "serial_port", default="/dev/cu.usbmodem11")
    params.mac_address   = patch.getstring("brainflow", "mac_address", default="")
    params.other_info    = patch.getstring("brainflow", "other_info", default="")
    params.serial_number = patch.getstring("brainflow", "serial_number", default="")
    params.ip_address    = patch.getstring("brainflow", "ip_address", default="")
    params.ip_protocol   = patch.getint("brainflow", "ip_protocol", default=0)
    params.timeout       = patch.getint("brainflow", "timeout", default=0)
    params.file          = patch.getstring("brainflow", "file", default="")

    monitor.success("Starting BrainFlow ...")

    BoardShim.disable_board_logger()
    # BoardShim.enable_board_logger()
    # BoardShim.enable_dev_board_logger()

    board = BoardShim(board_id, params)
    board.prepare_session()
    board.start_stream(45000, streamer_params)

    # get all data and remove it from internal buffer
    board.get_board_data()

    monitor.success("Connected to " + board.get_device_name(board_id))
    monitor.info("fsample =", board.get_sampling_rate(board_id))
    monitor.info("nchans  =", board.get_num_rows(board_id))

    ft_output.putHeader(board.get_num_rows(board_id), float(board.get_sampling_rate(board_id)), FieldTrip.DATATYPE_FLOAT32)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    """Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    """
    global patch, name, path, monitor
    global ft_host, ft_port, ft_output, delay, board_id, streamer_params, params, board
    global data

    if board.get_board_data_count()>0:
        data = np.transpose(board.get_board_data())
        ft_output.putData(data.astype(np.float32))
        monitor.debug("wrote " + str(len(data[:,1])) + " samples")
    else:
        # wait for a short time before trying again
        time.sleep(delay)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_forever():
    """Run the main loop forever
    """
    global monitor
    while True:
        monitor.loop()
        _loop_once()


def _stop():
    """Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    """
    global board
    board.stop_stream()
    board.release_session()


if __name__ == "__main__":
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
