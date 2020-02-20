import bitalino
import numpy as np
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation


sfreq = 1000
# read 500 samples on each call to the bitalino
nsamples = int(np.ceil(0.5 * sfreq))
# number of datapoints to display
xrange = int(np.ceil(5 * sfreq))

# connect to Bitalino and start data acquisition, HAS BEEN TESTED WITH BUTTON
# BIT ON INPUT CHANNEL 1
macAddress = '20:16:12:22:22:26'
device = bitalino.BITalino(macAddress)
device.start(sfreq, [1])
print('started data acquisition')


class SignalPlotter():

    def __init__(self, ax, xrange):
        self.ax = ax
        self.ax.set_ylim(-1, 2)
        self.xrange = xrange
        self.xs = list(range(0, xrange))
        self.ys = [0] * xrange
        # blank line will be updated during plotting
        self.line, = self.ax.plot(self.xs, self.ys)

    # update line on each call to this function
    def plot(self, data):
        self.ax.figure.canvas.draw()
        self.ys.extend(data)
        self.ys = self.ys[-self.xrange:]
        print(self.ys)
        self.line.set_ydata(self.ys)
        return self.line,

def fetch_data():
    data = device.read(nsamples)[:, 1].tolist()
    print(data)
    yield data
    
# instantiate fidure and SignalPlotter
fig, ax = plt.subplots()
plotter = SignalPlotter(ax, xrange)

# call SignalPlotter.plot() periodically to update the figure with fresh data
# from the bitalino, provided by the generator function
ani = animation.FuncAnimation(fig, plotter.plot, fetch_data,
                              interval=500, blit=True, repeat=True)

plt.show()