# EEG Processing Module

The goal of this module is to read EEG data from the FieldTrip buffer, to Fourier transform it and compute power in specific frequency bands. The power in each frequency band in each channel is written as control values to the Redis buffer.

This module implements automatic gain control by tracking (over time) the maximal and minimal value and scaling the output within this range. While the module is running, the automatic gain control can be frozen, re-initialized or adjusted (increased or decreased) with key-presses.
