LaunchControl module
====================

The purpose of this module is to provide a simple virtual synthesizer using the Raspberry Pi audio output.

** VCO - voltage controlled oscillator **

The VCO generates a simultaneous sine-, triangle-, saw- and square-wave signal, which are mixed into the audio output. It has one input control for the pitch and four input controls for the mixer.

** LFO - low frequency oscillator **

The LFO shapes the audio envelope. The LFO has two input controls for the frequency and the depth.

** VCA - voltage controlled amplifier **

The VCA shapes the audio envelope. The VCA has a single input controls for the attenuation.

** NOT YET IMPLEMENTED: ADSR - attack, decay, sustain, release **

The ADSR takes a trigger as input and generates a continuous envelope as output. It has four input controls.

** NOT YET IMPLEMENTED: VCF - voltage controlled filter **

The filter can be toggled between lowpass, highpass and bandpass filtering of the audio signal. It has two input controls for the frequency and bandwidth.

** Requirements **

The REDIS buffer should be running.
A pair of speakers or headphones should be connected to the Raspberry Pi audio output.
