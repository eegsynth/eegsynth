# Karlstad patch

This patch is for the performance in Karlstad on Saturday 25 May, 2019.

## Modules

You should start by connecting the electrodes to the performer and
the amplifier, and starting the OpenBCI GUI application with the
proper settings. Subsequently you can start the EEG data stream and
start the LSL stream.

The EEGsynth modules should then be started in the following order:

1. redis.sh
2. buffer.sh
3. lsl2ft.sh
4. inputcontrol.sh
5. plotsignal.sh
6. plotspectral.sh
7. spectral.sh
8. historycontrol.sh
9. postprocessing.sh
10. outputmidi.sh
11. outputartnet.sh
