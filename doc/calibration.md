# Calibration

The EEGsynth uses various control signals that have a different units and different absolute scaling. For example, MIDI values are between 0 and 127, OSC values are often (by convention) between 0 and 1, and EEG values are typically between -100 and +100 microvolt. Note that this is not only a problem for the EEGsynth, real-world modular synthesizers also use different [control voltage](https://en.wikipedia.org/wiki/CV/gate#CV) ranges.

To facilitate the interoperability between modules, we follow the convention that - whenever values are absolutely bounded between a known minimum and maximum - we scale the control values in Redis as a floating point value between 0 and 1. If another scaling is needed, e.g. for MIDI output, the control values can be read from Redis and scaled up to the desired level.

Some of the control values are not bounded, e.g. when spectral power is computed from the EEG signal. To use such control signals, they need to be calibrated and rescaled to predictable values using one of the following modules.

* [postprocessing](https://github.com/eegsynth/eegsynth/tree/master/module/postprocessing)
* [normalizecontrol](https://github.com/eegsynth/eegsynth/tree/master/module/normalizecontrol)
* [calibration](https://github.com/eegsynth/eegsynth/tree/master/module/calibration)
* [quantizer](https://github.com/eegsynth/eegsynth/tree/master/module/quantizer)

Related to this is that the [smoothing](https://github.com/eegsynth/eegsynth/tree/master/module/smoothing) module can be used to compute a smoothed version of specific control values.
