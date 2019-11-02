# Akusmata - macOS

This is a patch intended to transform EEG power in different
physiological bands from a single EEG channel into harmonics using
the Verbos Harmonic Oscillator. The individual alpha band is selected
using plotspectral, the delta, theta and beta bandds have a fixed
ferquency range.

All processing is done locally, except for the slew limiter (which
is done on the linux lapotop, just prior to sending the MIDI to the
endorphones). All control signals are stored in Redis running on
the linux laptop.

The patch running on the macbook uses channel 2, the patch running
on teh linux laptop is using channel 1. Note that these channels
are from two different amplifiers, attached to two performers.

