# Synchronization Module

The goal of this module is to use a continuous control value from the REDIS buffer for synchronization. The rate between synchronization events scales with the control value. The output of this module is sent as event to the REDIS buffer, as trigger to the serial CV/Gate hardware and as clock message to MIDI.

The MIDI clock ticks are always send 24 times per quarter note. The Serial and Redis triggers are sent once per note, or more frequently if you increase the step value. Allowed step values are 1,2,3,4,6,8,12,24. You can shift the Serial and Redis triggers with a certain amount of MIDI clock ticks using the adjust value (between -12 and 12).

The rate is limited between 40 and 240 beats per minute.

The multiplier is exponentially mapped as 2^value and quantized to an integer division or multiplication. For example, the values -2,-1,0,1,2 are mapped to 1/4,1/2,1,2,4.

The pulselength for the USB to CV/Gate can be specified, but will be limited between 5 ms and half a MIDI clock tick (which is 1/24 of a quarternote).  

## Requirements

The rate should be expressed in beats per minute.
The REDIS buffer should be running.
The MIDI port and serial port will be opened when required.

## Software Requirements

Python 2.x
Redis package for Python
mido
