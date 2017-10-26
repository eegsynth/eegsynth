# USB to CV/Gate

![photo](eegsynth_cvgate_mcp4725.jpg)

This is a one-channel version of a CV/Gate controller. It comprises of an Arduino Nano combined with a 12-bit DAC module. The output voltage is between 0 and 5 V, or slightly less. The maximum output voltage depends on the output of your USB port and of the voltage controller in the Arduino Nano.

This hardware works well with the *outputcvgate* Python module.

The Arduino code for the firmware of this device can be found on [github](https://github.com/robertoostenveld/arduino/tree/master/eegsynth_cvgate_mcp4725).
