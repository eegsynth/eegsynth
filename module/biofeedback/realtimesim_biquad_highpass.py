# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 15:50:56 2019

@author: John Doe
"""

import numpy as np


# test signal
path = r'C:\Users\JohnDoe\surfdrive\Beta\data\RESP\Bitalino\abele_zombies_spider_chest.txt'
signal = np.loadtxt(path)[:, -1]
samp_freq  = 1000
data_type = signal.dtype
MAX_VAL = abs(np.iinfo(data_type).min)

# parameters
buffer_len = int(np.ceil(0.1 * samp_freq))
pole_coef = 0.95
n_buffers = len(signal)//buffer_len

# allocate input and output buffers
input_buffer = np.zeros(buffer_len, dtype=data_type)
output_buffer = np.zeros(buffer_len, dtype=data_type)

# state variables
def init():

    # define filter parameters
    global b_coef, a_coef, HALF_MAX_VAL, GAIN, N_COEF
    GAIN = 0.8
    HALF_MAX_VAL = MAX_VAL // 2
    b_coef = [HALF_MAX_VAL, -2 * HALF_MAX_VAL, HALF_MAX_VAL]
    a_coef = [HALF_MAX_VAL,
              int(-2 * pole_coef * HALF_MAX_VAL),
              int(pole_coef * pole_coef * HALF_MAX_VAL)]
    N_COEF = len(a_coef)

    # declare variables used in 'process'
    global y, x
    y = np.zeros(N_COEF, dtype=data_type)
    x = np.zeros(N_COEF, dtype=data_type)

    return
# the process function!
def process(input_buffer, output_buffer, buffer_len):

    # specify global variables modified here
    global y, x

    # process one sample at a time
    for n in range(buffer_len):

        # apply input gain
        x[0] = int(GAIN * input_buffer[n])

        # compute filter output
        output_buffer[n] = int(b_coef[0] * x[0] / HALF_MAX_VAL)
        for i in range(1, N_COEF):
            # TODO: add prev input and output according to block diagram
            output_buffer[n] += 0

        # update state variables
        y[0] = output_buffer[n]
        for i in reversed(range(1, N_COEF)):
            # TODO: shift prev values
            x[i] = 0
            y[i] = 0
            

init()
# simulate block based processing
signal_proc = np.zeros(n_buffers*buffer_len, dtype=data_type)
for k in range(n_buffers):

    # index the appropriate samples
    input_buffer = signal[k*buffer_len:(k+1)*buffer_len]
    process(input_buffer, output_buffer, buffer_len)
    signal_proc[k*buffer_len:(k+1)*buffer_len] = output_buffer

"""
Visualize / test
"""
import matplotlib.pyplot as plt

ALPHA = 0.75     # transparency for plot

plt.figure()
plt.plot(np.arange(len(signal)) / samp_freq, signal, 'tab:blue', label="original", alpha=ALPHA)
plt.plot(np.arange(len(signal_proc)) / samp_freq, signal_proc, 'tab:orange', label="biquad", alpha=ALPHA)
plt.xlabel("Time [seconds]")
plt.grid()
f = plt.gca()
f.axes.get_yaxis().set_ticks([0])
plt.legend()

plt.show()