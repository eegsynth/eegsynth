# Calibration

The EEGsynth uses various control signals that have a different units and different absolute 
scaling. For example, MIDI values are between 0 and 127, OSC values are often (by convention) 
between 0 and 1, and EEG values are typically between -100 and +100 microvolt. 
Note that this is not only a problem for the EEGsynth; real-world modular synthesizers also 
use different [control voltage](https://en.wikipedia.org/wiki/CV/gate#CV) ranges.

To facilitate the interoperability between modules, we follow the convention that whenever 
values are absolutely bounded between a known minimum and maximum we scale the control values 
in Redis as a floating point value between 0 and 1. If another scaling is needed, e.g. for MIDI
output, the control values can be read from Redis and scaled up to the desired level.

Some of the control values are not bounded, e.g. when spectral power is computed from the EEG 
signal. To use such control signals, they need to be calibrated and rescaled to predictable 
values using one of the following modules:

* The [calibration module](../module/calibration) to scale, offset and compress/expand data.
* The [historycontrol module](../module/historycontrol) to calculate properties over history of control values,
such as the median and the standard deviation, using a sliding window. To be used together with
the [postprocessing module](../module/postprocessing) or the [calibration module](../module/calibration) 
to scale the data. 
* The [quantizer module](../module/quantizer).

## References for Control voltage range for external devices

### Endorphins Shuttle Control

The EEGsynth uses the [Endorphins Shuttle Control](https://www.modulargrid.net/e/endorphin-es-shuttle-control) 
optimally with the +/-5V pitchweel setting, which is the maximum range supported by the Shuttle Control. 
For more info see [this blogpost](http://www.eegsynth.org/?p=480) as well as [the readme](../module/endorphines/README.md).
Through the endorphins .ini the output control voltage can be restricted to 0-5V.

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
