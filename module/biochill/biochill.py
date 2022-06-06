#!/usr/bin/env python

# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2017-2022 EEGsynth project
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
from scipy.signal import sosfilt_zi, sosfilt


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
from EEGsynth import bessel_highpass, bessel_bandpass


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

        self.channel = self.patch.getint("input", "channel")
        self.key_biofeedback = self.patch.getstring("output", "key_biofeedback")
        sfreq = hdr_input.fSample

        self.stride = self.patch.getint("input", "stride")

        self.window_biofeedback = self.patch.getint("input", "window_biofeedback")    # seconds
        if self.stride >= self.window_biofeedback:
            raise RuntimeError("stride must be shorter than window_biofeedback.")
        self.window_biofeedback = int(np.ceil(self.window_biofeedback / self.stride))    # blocks of size stride

        self.window_target = self.patch.getint("input", "window_target")    # seconds
        if self.stride >= self.window_target:
            raise RuntimeError("stride must be shorter than window_target.")
        self.window_target = int(np.ceil(self.window_target / self.stride))    # blocks of size stride

        if self.window_biofeedback >= self.window_target:
            raise RuntimeError("window_biofeedback must be shorter than window_target.")

        self.buffer = np.zeros(self.window_target)

        self.stride = int(np.ceil(self.stride * sfreq))    # convert to samples for indexing

        if hdr_input.nSamples < self.stride:
            self.begsample = 0
            self.endsample = self.stride - 1
        else:
            self.begsample = hdr_input.nSamples - self.stride
            self.endsample = hdr_input.nSamples - 1

        # Initialize filters (hardcode frequencies to prevent accidental changes
        # in inifile, and express them as bpm / 60 for readability)
        self.sos_hp = bessel_highpass(15 / 60, sfreq, 4)
        self.zi_hp = sosfilt_zi(self.sos_hp)

        self.sos_bp = bessel_bandpass(4 / 60, 12 / 60, sfreq, 2)
        self.zi_bp = sosfilt_zi(self.sos_bp)

        # self.previoustime = time.time()    # use to debug/monitor timing of calls to compute_biofeedback()

        while True:
            self.monitor.loop()
            self.compute_biofeedback()


    def stop(self):
        self.ft_input.disconnect()
        self.monitor.success("Disconnected from input FieldTrip buffer")
        sys.exit()


    def biofeedback_function(self, x, target):
        """Hill equation.

        https://en.wikipedia.org/wiki/Hill_equation_(biochemistry). Biofeedback
        target is equivalent to K parameter.

        Parameters
        ----------
        x : float
            Input value.
        target : float
            The value of x at which half of the maximum reward is obtained. In
            units of x.
        Returns
        -------
        y : float
            Biofeedback value in the range [0, 1].
        """
        if x < 0:
            return 0

        Vmax = 1    # Upper limit of y values
        n = 3    # Hill coefficient, determines steepness of curve
        y = Vmax * x**n / (target**n + x**n)
        return y


    def compute_biofeedback(self):

        hdr_input = self.ft_input.getHeader()
        if (hdr_input.nSamples - 1) < self.begsample - self.stride:
            raise RuntimeError("Buffer reset detected.")
        if (hdr_input.nSamples - 1) < self.endsample:
            time.sleep(.1)
            return    # there are not yet enough samples in the buffer

        data = self.ft_input.getData([self.begsample, self.endsample]).astype(np.double)
        data = data[:, self.channel]

        self.monitor.info("Processing sample {0} to {1}".format(self.begsample, self.endsample))

        reward, self.zi_bp = sosfilt(self.sos_bp, data, zi=self.zi_bp)
        nonreward, self.zi_hp = sosfilt(self.sos_hp, data, zi=self.zi_hp)

        self.buffer = np.roll(self.buffer, -1)    # shift elements in buffer on index to the left
        current_biofeedback = np.sum(np.abs(reward)**2 - np.abs(nonreward)**2)
        self.buffer[-1] = current_biofeedback    # replace buffer element that rolled over after shift (from first to last position)

        target = np.percentile(self.buffer, 95)    # use entire buffer to track median (over window_target blocks of stride seconds)
        biofeedback = np.sum(self.buffer[-self.window_biofeedback:])    # use last window_biofeedback blocks of stride seconds for computation of current biofeedback score

        biofeedback_score = self.biofeedback_function(biofeedback, target)

        # Publish the biofeedback value on the Redis channel.
        self.patch.setvalue(self.key_biofeedback, biofeedback_score)
        print("Biofeedback={0}".format(biofeedback_score))

        #t = time.time()
        #print(t - self.previoustime)
        #self.previoustime = t

        self.begsample += self.stride
        self.endsample += self.stride


if __name__ == "__main__":
    biofeedbackloop = BreathingBiofeedback(path, name)
    try:
        biofeedbackloop.start()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        biofeedbackloop.stop()
