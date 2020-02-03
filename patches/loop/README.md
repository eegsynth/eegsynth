# Ableton Loop

This directory contains some of the patches for the workshop at [Ableton Loop](Berlin, April 24–26 2020) in Berlin, April 24–26 2020. During the workshop we combine electrophysiological signals from the brain, muscle, eye and heart with electronic music and analog synthesizers.

# Technical details

The patch starts with the signals from a 4-channel [OpenBCI Gangion amplifier](http://www.eegsynth.org/?p=2034). The bipolar ExG channels are connected like this

1. EEG (brain)
2. EMG (muscle)
3. EOG (eye)
4. ECG (heart)

Each of the electrophysiological signals is processed separately using settings optimized for the respective signal characteristics. The combined raw data for the 4 signals is represented in buffer `1972`. The processed data for each type of signal is represented in

4. EEG (brain) in 1973
3. EMG (muscle) in 1974
1. EOG (eye) in 1975
2. ECG (heart) in 1976

The brain and muscle signals are converted into continuous control channels. From the brain signal the different frequency bands (delta, theta, alpha, beta, gamma) are detected. Instantaneous triggers are detected for the eye blinks and heart beats. The heart signal is also converted into a continuous heart rate control channel.
