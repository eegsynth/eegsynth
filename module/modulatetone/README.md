# Modulatetone module

The modulatetone module uses a number of control signals to modulate the amplitude of a number of pure sinewave tones. The sinewave tones are superimposed and played as audio. A receiving device (e.g., another computer running Max, a Bela, or a OWL Modular) can demodulate the different tones and use them as separate control signals.

This allows transmitting multiple controls over a mono or stereo analog audio line.

## Optimal carrier tones frequencies

The example `.ini` file shows how to configure the carrier tone frequencies. It is important to consider the potential effect of spectral leakage if the frequencies do not match with the characteristics on the receiving side. When the decoding is done with an FFT length of 1024 samples and 44100 Hz sampling rate, integer multiples of 44100/1024=43.066 Hz are optimal to avoid spectral leakage. When the decoding is done with an FFT length of 1024 samples and 48000 Hz sampling, integer multiples of 48000/1024=46.875 Hz are optimal.
