#!/usr/bin/env python

# Unicorn2ft module that streams data from a Unicorn Hybrid Black EEG system
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

import os
import sys
import time
import serial
import struct
import numpy as np
import serial.tools.list_ports
from fuzzywuzzy import process

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0, os.path.join(path, '../../lib'))
import FieldTrip
import EEGsynth


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor
    global prefix, ft_host, ft_port, ft_output, timeout, blocksize, nchan, fsample, serialdevice, start_acq, stop_acq, start_sequence, stop_sequence, s, response

    try:
        ft_host = patch.getstring('fieldtrip', 'hostname')
        ft_port = patch.getint('fieldtrip', 'port')
        monitor.info('Trying to connect to buffer on %s:%i ...' % (ft_host, ft_port))
        ft_output = FieldTrip.Client()
        ft_output.connect(ft_host, ft_port)
        monitor.info("Connected to output FieldTrip buffer")
    except:
        raise RuntimeError("cannot connect to output FieldTrip buffer")

    # get the options from the configuration file
    timeout = patch.getfloat('unicorn', 'timeout', default=5)
    blocksize = patch.getfloat('unicorn', 'blocksize', default=0.2) # write blocks of 0.2 seconds, i.e., 50 samples

    # write the header information to the FieldTrip buffer
    nchan = 16
    fsample = 250
    ft_output.putHeader(nchan, fsample, FieldTrip.DATATYPE_FLOAT32)

    monitor.success("connecting to Unicorn...")

    # get the specified serial device, or the one that is the closest match
    serialdevice = patch.getstring('unicorn', 'device')
    serialdevice = EEGsynth.trimquotes(serialdevice)
    serialdevice = process.extractOne(serialdevice, [comport.device for comport in serial.tools.list_ports.comports()])[0] # select the closest match

    start_acq      = [0x61, 0x7C, 0x87]
    stop_acq       = [0x63, 0x5C, 0xC5]
    start_response = [0x00, 0x00, 0x00]
    stop_response  = [0x00, 0x00, 0x00]
    start_sequence = [0xC0, 0x00]
    stop_sequence  = [0x0D, 0x0A]

    try:
        s = serial.Serial(serialdevice, 115200, timeout=timeout)
        monitor.success("connected to serial port " + serialdevice)
    except:
        raise RuntimeError("cannot connect to serial port " + serialdevice)

    # start the data stream
    s.write(start_acq)

    response = s.read(3)
    if response != b'\x00\x00\x00':
        raise RuntimeError("cannot start data stream")

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print("LOCALS: " + ", ".join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    '''
    global patch, name, path, monitor
    global prefix, ft_host, ft_port, ft_output, timeout, blocksize, nchan, fsample, serialdevice, start_acq, stop_acq, start_sequence, stop_sequence, s, response

    nsample = int(blocksize*fsample)
    dat = np.zeros((nsample,nchan))

    for sample in range(0,nsample):
        # read one block of data from the serial port
        payload = s.read(45)

        # check the start and end bytes
        if payload[0:2] != b'\xC0\x00':
            raise RuntimeError("invalid packet")
        if payload[43:45] != b'\x0D\x0A':
            raise RuntimeError("invalid packet")

        battery = 100*float(payload[2] & 0x0F)/15

        eeg = np.zeros(8)
        for ch in range(0,8):
            # unpack as a big-endian 32 bit signed integer
            eegv = struct.unpack('>i', b'\x00' + payload[(3+ch*3):(6+ch*3)])[0]
            # apply two’s complement to the 32-bit signed integral value if the sign bit is set
            if (eegv & 0x00800000):
                eegv = eegv | 0xFF000000
            eeg[ch] = float(eegv) * 4500000. / 50331642.

        accel = np.zeros(3)
        # unpack as a little-endian 16 bit signed integer
        accel[0] = float(struct.unpack('<h', payload[27:29])[0]) / 4096.
        accel[1] = float(struct.unpack('<h', payload[29:31])[0]) / 4096.
        accel[2] = float(struct.unpack('<h', payload[31:33])[0]) / 4096.

        gyro = np.zeros(3)
        # unpack as a little-endian 16 bit signed integer
        gyro[0] = float(struct.unpack('<h', payload[27:29])[0]) / 32.8
        gyro[1] = float(struct.unpack('<h', payload[29:31])[0]) / 32.8
        gyro[2] = float(struct.unpack('<h', payload[31:33])[0]) / 32.8

        counter = struct.unpack('<L', payload[39:43])[0]

        # collect the data that will be sent to the FieldTrip buffer
        dat[sample,0:8]   = eeg
        dat[sample,8:11]  = accel
        dat[sample,11:14] = gyro
        dat[sample,14]    = battery
        dat[sample,15]    = counter

    # write the segment of data to the FieldTrip buffer
    ft_output.putData(dat.astype(np.float32))
    monitor.info('wrote samples %d' % counter)


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay'))


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global s, stop_acq
    # stop the data stream and close the serial port
    s.write(stop_acq)
    monitor.success("Closing serial port")
    s.close()


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    sys.exit()
