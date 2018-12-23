# Generate clock module

The goal of this module is to generate regular clock signals. The rate of these clock signals is determined by a continuous control value. The output is sent as message to the Redis buffer and as clock ticks to MIDI. The Redis and MIDI messages are synchronous.

The MIDI clock ticks are always send 24 times per quarter note, or 96 times per whole note. The MIDI clock signals will start ticking whenever the *play* parameter switches to true. This can be hardcoded as "1" in the ini file, but can also be mapped to a toggle button that is represented as control channel in Redis. The MIDI start signal will be sent whenever the *start* parameter switches to true. This can be hardcoded as "1" in the ini file, but can also be mapped to a toggle button that is represented as control channel in Redis. The MIDI stop signal will be sent whenever the *start* parameter switches to false. If you do not want the MIDI start and stop signal to be sent (e.g. when your MIDI device device has a button), you should leave the *start* parameter empty.

The rate of the Redis messages is controlled by the *ppqn* (pulse per quarter note) parameter. Since Redis messages are aligned with the MIDI clock ticks, only integer divisors are possible. You can specify values of 1,2,3,4,6,8,12,24, where 1 means one pulse per quarter note. You can shift the Redis messages relative to the MIDI clock ticks by a quarter note using the *shift* parameter (between -12 and 12).

The clock rate is limited between 30 and 240 beats per minute.

## Sending MIDI clock messages and starting/stopping the external MIDI device

Sending MIDI clock messages is in principle independent from whether the external MIDI sequencer is started or not. There are cases where you want to start the MIDI sequencer together with the sequencer (e.g. with the Endorphines eurorack module), but there are also cases when you want to start the MIDI sequencer by hand (e.g. with the Korg Volca synthesizers).

The following examples demonstrate how to configure the *play* and the *start* parameter in the ini file for some scenarios.

### Start both the clock and the sequencer immediately

This starts both as soon as the EEGsynth module starts running.

  [midi]
  play=1
  start=1

### One button to start both the clock and the sequencer

This allows you to press a single toggle button to start (and stop) both.

  [midi]
  play=launchcontrol.note041
  start=launchcontrol.note041

### Separate buttons for the clock and the sequencer

This allows you to start both the clock and the external MIDI device separately. If *play* is enabled and *start* is not, you could use a physical start button on the MIDI device. If *play* would not be enabled but *start* is, the external MIDI device would start running on its own clock rate.

  [midi]
  play=launchcontrol.note041
  start=launchcontrol.note042

### The clock ticks immediately, but start/stop uses a toggle button

In this example the clock is started as soon as the module starts, and the start/stop is controlled by a button in the EEGsynth. If you have daisy chained multiple MIDI devices, this allows you to start/stop all of them at the same time.

  [midi]
  play=1
  start=launchcontrol.note042

### The clock ticks immediately, start/stop are not sent

The following is useful if your MIDI device has a physical start button.

  [midi]
  play=1
  start=

### The clock always ticks, start/stop are not sent

The following is useful if you want to be able to switch between the EEGsynth clock and the internal clock of the MIDI device. Starting the sequence has to be done with the physical start button on the MIDI device itself.

  [midi]
  play=launchcontrol.note041
  start=
