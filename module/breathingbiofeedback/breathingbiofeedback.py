#!/usr/bin/env python3

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2020 EEGsynth project
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

import configparser
import argparse
import os
import redis
import sys
import time
import numpy as np
from scipy.signal import lfilter_zi, lfilter


if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(sys.executable)[-1]
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
EEGsynth import butter_highpass, butter_bandpass


class BreathingBiofeedback:

    def __init__(self, path, name):

        # Configuration.
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--inifile",
                            default=os.path.join(path, name + '.ini'),
                            help="name of the configuration file")
        args = parser.parse_args()

        config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        config.read(args.inifile)

        # Redis.
        try:
            rds = redis.StrictRedis(host=config.get('redis', 'hostname'),
                                    port=config.getint('redis', 'port'),
                                    db=0, charset='utf-8',
                                    decode_responses=True)
        except redis.ConnectionError as e:
            raise RuntimeError(e)

        self.patch = EEGsynth.patch(config, rds)    # combine patching from configuration file and Redis.

        # Monitor.
        self.monitor = EEGsynth.monitor(name=name,
                                        debug=self.patch.getint('general', 'debug'))

        # FieldTrip.
        try:
            ft_host = self.patch.getstring('fieldtrip', 'hostname')
            ft_port = self.patch.getint('fieldtrip', 'port')
            self.monitor.success("Trying to connect to buffer on {0}{1}.".format(ft_host, ft_port))
            self.ft_input = FieldTrip.Client()
            self.ft_input.connect(ft_host, ft_port)
            self.monitor.success('Connected to input FieldTrip buffer.')
        except:
            raise RuntimeError("Cannot connect to input FieldTrip buffer.")


    def start(self):

        hdr_input = None
        start = time.time()
        while hdr_input is None:
            self.monitor.info("Waiting for data to arrive.")
            if (time.time() - start) > self.patch.getfloat('fieldtrip', 'timeout', default=30):
                raise RuntimeError("Timeout while waiting for data.")
            time.sleep(0.1)
            hdr_input = self.ft_input.getHeader()

        self.monitor.info("Data arrived.")

        sfreq = hdr_input.fSample

        self.window = int(np.rint(sfreq * self.patch.getfloat("input", "window")))    # must be a multiple of stride
        self.stride = int(np.rint(sfreq * self.patch.getfloat("input", "stride")))

        if hdr_input.nSamples < self.stride:
            self.begsample = 0
            self.endsample = self.stride - 1
        else:
            self.begsample = hdr_input.nSamples - self.stride
            self.endsample = hdr_input.nSamples - 1

        self.biofeedback_target = self.patch.getfloat("biofeedback", "target")
        self.channel = self.patch.getint("input", "channel")
        self.key_biofeedback = self.patch.getstring("output", "key_biofeedback")

        self.reward_buffer = np.zeros(self.window)
        self.nonreward_buffer = np.zeros(self.window)

        # Initialize filters (hardcode frequencies to prevent accidental changes
        # in inifile, and express them as bpm / 60 for readability)
        self.b_hp, self.a_hp = butter_highpass(15 / 60, sfreq, 6)
        self.zi_hp = lfilter_zi(self.b_hp, self.a_hp)

        self.b_bp, self.a_bp = butter_bandpass(4 / 60, 10 / 60, sfreq, 4)
        self.zi_bp = lfilter_zi(self.b_bp, self.a_bp)

        while True:
            self.monitor.loop()
            self.compute_biofeedback()


    def stop(self):
        self.ft_input.disconnect()
        self.monitor.success("Disconnected from input FieldTrip buffer")
        sys.exit()


    def biofeedback_function(self, x):
        """
        Parameters
        ----------
        x : float
            Physiological input value.
        Returns
        -------
        y : float
            Biofeedback value in the range [0, 1].
        """
        x0 = 1e-5
        x1 = self.biofeedback_target
        y0 = 1e-5
        y1 = 1

        if x >= x1:
            return y1    # cap at target
        y = y0 + (x - x0) * ((y1 - y0) / (x1 - x0))    # linear mapping

        return y


    def compute_biofeedback(self):

        hdr_input = self.ft_input.getHeader()
        if (hdr_input.nSamples - 1) < self.begsample:
            raise RuntimeError("Buffer reset detected.")
        if (hdr_input.nSamples - 1) < self.endsample:
            self.monitor.info("Waiting for data to arrive.")    # there are not yet enough samples in the buffer
            return

        data = self.ft_input.getData([self.begsample, self.endsample]).astype(np.double)
        data = data[:, self.channel]

        self.monitor.info("Processing sample {0} to {1}".format(self.begsample, self.endsample))

        reward, self.zi_bp = lfilter(self.b_bp, self.a_bp, data, zi=self.zi_bp)
        self.reward_buffer = np.roll(self.reward_buffer, -self.stride)
        self.reward_buffer[-self.stride:] = reward

        nonreward, self.zi_hp = lfilter(self.b_hp, self.a_hp, data, zi=self.zi_hp)
        self.nonreward_buffer = np.roll(self.nonreward_buffer, -self.stride)
        self.nonreward_buffer[-self.stride:] = nonreward

        amp_reward = np.sum(np.abs(self.reward_buffer)**2)    # Lotte et al. (2011), 10.1109/CCMB.2011.5952105
        amp_nonreward = np.sum(np.abs(self.nonreward_buffer)**2)

        biofeedback = amp_reward / amp_nonreward
        biofeedback = self.biofeedback_function(biofeedback)

        # Publish the biofeedback value on the Redis channel.
        self.patch.setvalue(self.key_biofeedback, biofeedback)

        self.begsample += self.stride
        self.endsample += self.stride


if __name__ == "__main__":
    biofeedbackloop = BreathingBiofeedback(path, name)
    try:
        biofeedbackloop.start()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        biofeedbackloop.stop()
