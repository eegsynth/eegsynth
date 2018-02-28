# Spectral Plotting Module

The purpose of this module is to visualize the spectrum content of a signalin realtime. It has added functionality for display and control:
The displayed spectrum has some smoothing for smooth fluctuations over time.
Two frequency bands (red and blue) can be selected visually (e.g. using a LaunchControl) by setting their center and bandwidth. These frequencybands are updated in Redis, allowing real-time control of the frequency band of spectral analysis (spectral module).

## Software Requirements

Python 2.7.x
pyqtgraph
