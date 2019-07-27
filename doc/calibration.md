# Scaling and calibration

The EEGsynth uses various control signals that have a different units and different absolute scaling. For example, MIDI values are between 0 and 127, OSC values are often (by convention) between 0 and 1, and EEG values are typically between -100 and +100 microvolt. Note that this is not only a problem for the EEGsynth; real-world modular synthesizers also use different [control voltage](https://en.wikipedia.org/wiki/CV/gate#CV) ranges.

To facilitate the interoperability between modules, we follow the convention that whenever values are absolutely bounded between a known minimum and maximum we scale the control values in Redis as a floating point value between 0 and 1. If another scaling is needed, e.g. for MIDI output between 0 and 127, the control values can be read from Redis and scaled up to the desired level.

Some of the control values are not bounded, e.g. when spectral power is computed from the EEG signal. To use such control signals, they need to be calibrated and rescaled to predictable values using one of the following modules:

- The [postprocessing module](../module/compressor) to linearly or non-linearly transform control values.
- The [compressor module](../module/compressor) to compress or expand control values.
- The [historycontrol module](../module/historycontrol) to calculate properties from the history of control values,
  such as the median and the standard deviation, using a sliding window. Can be used together with the [postprocessing module](../module/postprocessing) for dynamic scaling between the minimum and maximum values.
- The [quantizer module](../module/quantizer) to map continuous values onto a predefined discrete scale.

## Control Voltage range for external hardware devices

### Endorphins Shuttle Control

The EEGsynth uses the [Endorphines Shuttle Control](https://www.modulargrid.net/e/endorphin-es-shuttle-control) optimally with the +/-5V pitchweel setting, which is the maximum range supported by the Shuttle Control. For more info see [this blogpost](http://www.eegsynth.org/?p=480) as well as [the readme](../module/endorphines/README.md). Through the endorphines .ini the output control voltage can be restricted to 0-5V.

### Doepfer MIDI to CV/Gate interfaces

The Doepfer [A-190-2, A-190-3, MCV4 and Dark Link](doepfer.md) have a 0-5 V output for CV1, CV3 and CV4, with 1 V/octave for the pitch on CV1. The CV2 (pitch bend) can be set to -2.5 to +2.5V (default) or to 0-5V using an internal jumper.

### Erebus Dreadbox

The Erebus Dreadbox analogue synthesizer has the following specific patching specifications according to the [manual](http://www.dreadbox-fx.com/wp-content/uploads/2016/04/erebus_manual_v2.pdf):

```
INPUT OSC pitch: +/- 12V, 1V/oct
INPUT VCA: +/- 5V

INPUT LFO(rate): 0-5V
INPUT PW: 0-5V
INPUT Echo: 0-5V, best at 0-2.5V

OUTPUT OSC: 1V/oct, converted from MIDI if needed
OUTPUT ADSR: 0-6.6V, depending on depth setting
OUTPUT LFO: +/- 5V
```

### Arturio Microbrute

The [Microbrute](https://www.arturia.com/products/hardware-synths/microbrute/overview) has the following specifications, according to a nice article [here](http://www.hars.de/2016/01/microbrute-eurorack.html):

```
INPUT/OUTPUT OSC pitch: 0-10V, 1V/oct
OUTPUT LFO: +/- 5V
OUTPUT ADSR: 0-4.5V
```

I found no further specifications on the other input patches, i.e. Sub/PWM etc., but given that they are well-controlled by its own LFO, I would think they work well for +/-5V as well.
