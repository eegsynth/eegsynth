# Doepfer MIDI to CV/Gate interfaces

Doepfer has a number of very similar MIDI to CV/Gate interfaces. The [MCV4](http://www.doepfer.de/mcv4.htm) is a stand-alone box. The [A-190-2](http://www.doepfer.de/a1902.htm) is the modular version of the MCV4. The [A-190-3](http://www.doepfer.de/a1903.htm) is similar to the A-190-2, but has an additional USB interface and a different behavior of the LED. The A-190-3 is the modular version of the [Dark Link](http://www.doepfer.de/Dark_Link_e.htm), which is the MIDI interface of the [Dark Energy](http://www.doepfer.de/Dark_Energy_II_e.htm). All of these interfaces are controlled in nearly the same way and have the same core functionality.

## Output channels for the A-190-3 (from top to bottom)

### Gate

This is controlled by MIDI "note on" and "note off" messages, which switch the output between 0V and 5V.

### CV1

This is controlled by MIDI note messages. The range is 0 to +5V and it scales with 1V/Octave. The glide control (portamento) knob can be used for CV1.

As the range is 0-5V and the increment is 1V/octave, CV1 is restricted to 5 octaves and hence 60 MIDI notes from the 127.

You have to send the "note off" message prior to sending a new "note on" message, otherwise the pitch does not change.

### CV2

This is controlled by MIDI pitch bend. The range can be set to approximately -2.5 to +2.5V (default) or to approximately 0 to +5V using an internal jumper.

Pitch bend MIDI values go from -8192 to 8191. Since all other MIDI messages go from 0 to 127, the [outputmidi module](../module/outputmidi) shifts and scales the Redis values with an extra amount to map them onto the full output range.

### CV3

This is controlled by MIDI volume. The range is approximately 0 to +5V. According to [this documentation](http://www.indiana.edu/~emusic/etext/MIDI/chapter3_MIDI6.shtml) it corresponds to MIDI control 7.

### CV4

This is controlled by MIDI control change messages, free assignable controller in learn mode. The range is approximately 0 to +5V. The control change that CV4 responds to can be programmed.

## Programming the MIDI interface

It is required that you program the interface for CV1. Press the "Learn" button until the LED starts to blink. The first note that you send will determine the MIDI channel to which CV1 will respond, and the lowest MIDI pitch corresponding to 0V. Hence you should send the lowest note of the range that you will be using. With the command-line [sendmidi](https://github.com/gbevin/SendMIDI) application you could do:

```
sendmidi dev 'USB MIDI Dark Energy' ch 1 on 12 64
```

It is also required that you learn the interface to which MIDI control signal it should respond for CV4. You can do:

```
sendmidi dev 'USB MIDI Dark Energy' ch 1 cc 1 64
```

## Outputmidi configuration for A-190-3

The following configuration works well for [outputmidi](../module/outputmidi) in combination with the A-190-3. Here it is combined with 4 sliders in the [inputcontrol](../module/inputcontrol) graphical interface.

```
[trigger]
note=gui.cv1          ; the MIDI channel and the lowest note must be learned
pitchwheel=gui.cv2
control007=gui.cv3    ; this must be control #7
control001=gui.cv4    ; this must be learned
```

## Outputmidi configuration for MCV4

The following configuration works well for [outputmidi](../module/outputmidi) in combination with the MCV4. Here it is combined with 5 sliders in the [inputcontrol](../module/inputcontrol) graphical interface. The `cv1mod` slider allows for small adjustments to the CV1 voltage.

```
[trigger]
note=gui.cv1          ; the MIDI channel and the lowest note must be learned
pitchwheel=gui.cv1mod
aftertouch=gui.cv2
control007=gui.cv3    ; this must be control #7
control001=gui.cv4    ; this can be learned, the default is modulation, i.e. control #1
```
