# Demodulatetone module

The demodulatetone module takes an audio signal that contains one or multiple amplitude- or frequency-modulated tones, estimates the amount of modulation, and writes that as a control signal to Redis.

This module complements the `modulatetone` module.

## Optimal carrier tones frequencies

The example `.ini` file shows how to configure the carrier tone frequencies. It is important to consider the potential effect of spectral leakage if the frequencies do not match with the characteristics on the receiving side.

### Amplitude (de)modulation

With AM it is possible to use closely-spaced frequencies and code the amplitude of many control signals. To prevent spectral leakage, it is important to match the frequencies to those that can uniquely be demodulated. When the amplitude demodulation is done with an FFT window length of 1024 samples and 44100 Hz sampling rate, integer multiples of 44100/1024=43.066 Hz are optimal to avoid spectral leakage. When the amplitude demodulation is done with an FFT length of 1024 samples and 48000 Hz sampling, integer multiples of 48000/1024=46.875 Hz are optimal.

With AM it is also important to consider that any other change in ampliture, for example by changing the loudness of the audio input or th esensitivity of the microphone input will directly affect the scale of the demodulated control signals. You could use a reference tone with a fixed control value and the `postprocessing` module to to compensate for loudness differences.

### Frequency (de)modulation

With FM the number of control signals that can be coded is limited by the sampling frequency and by the speed at which the decoding has to happen. When using a demodulation with a 1024 sample window at 44100 Hz, the unique frequencies that can be represented have a spacing of 44100/1024=43.07 Hz. Coding control values with an amplitude resolution of 1/128 requires 128 unique frequencies. Consequently, with a 1024 samples window and a Nyquist frequency of 22050 Hz, the required bandwith per tone/control is 5512.5 Hz, allowing for up to 4 tones/controls per audio channel.
