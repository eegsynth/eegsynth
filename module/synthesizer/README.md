LaunchControl module
====================

The purpose of this module is to provide a simple virtual synthesizer using the Raspberry Pi audio output.

** VCO - voltage controlled oscillator **

The VCO generates a simultaneous triangle, saw and square wave signal, which are mixed into the audio output. It has one input control for the pitch and three input controls for the mixer.

** VCA - voltage controlled amplifier **

The VCA shapes the audio envelope. Each VCA has two input controls for the attenuator and the passthrough level.

** ADSR - attack, decay, sustain, release **

The ADSR takes a trigger as input and generates a continuous envelope as output. It has four input controls.

** VCF - voltage controlled filter **

The filter can be toggled between lowpass, highpass and bandpass filtering of the audio signal. It has two input controls for the frequency and bandwidth.

** Requirements **

The REDIS buffer should be running.
A pair of speakers or headphones should be connected to the raspberry Pi audio output.
