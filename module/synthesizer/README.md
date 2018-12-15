# LaunchControl Module

The purpose of this module is to provide a simple virtual synthesizer using the computer audio output. This virtual synthesizer consists of a few standard modules.

## VCO - voltage controlled oscillator

The VCO generates a simultaneous sine-, triangle-, saw- and square-wave signal, which are mixed into the audio output. It has one input control for the pitch and four input controls for the mixer.

## LFO - low frequency oscillator

The LFO shapes the audio envelope. The LFO has two input controls for the frequency and the depth.

## VCA - voltage controlled amplifier

The VCA shapes the audio envelope. The VCA has a single input controls for the attenuation.

## ADSR - attack, decay, sustain, release

The ADSR takes a trigger as input and generates a continuous envelope as output. It has input controls for A, D, S and R and for the trigger.
