# Recording

Although the primary use of the EEGsynth is to perform real-time
analysis and to use the control signals for direct feedback, there
are cases where it can be useful to record the data to disk. One
of these is when you want to optimize a certain signal processing
algorithm, another is if you want to replay the control signals to
try out different analog patches of a synthesizer or light system.

## Recordsignal

This module reads the physiological data from the FieldTrip buffer
and writes it to an EDF file, or to a WAV audio file.

This module will send a synchronization message to REDIS at regular
timepoints, with the current sample number in the file as the value.

## Recordcontrol

This module reads the control signals for selected channels from
the REDIS buffer and writes it to an EDF file, or to a WAV audio
file.

This module will send a synchronization message to REDIS at regular
timepoints, with the current sample number in the file as the value.

## Recordtrigger

This module subscribes to specific pubsub channels in REDIS and
writes a TSV file. Each row of the TSV file has the event name,
event value and the timestamp of the event (as date and time according
to the clock).

By default, this module will also write the synchronization messages
that are created by the recordsignal and recordcontrol modules.
This allows to  post-hoc synchronize the physiological and control
signal to each other and to other events.

## Playing recorded signals back

You can use the playbacksignal module to play physiological signals
from a file back to the FieldTrip buffer. This module will try to
play the signals in real time, i.e. with a speed that matches the
original recording.

You can use the playbackcontrol module to play control signals from
a file back to the REDIS buffer. This module will try to play the
signals in real time, i.e. with a speed that matches the original
recording.

## Simulating physiological and control signals

You can use the generatesignal and the generatecontrol modules to
generate physiological signals that are sent to the FieldTrip buffer,
or control signals that are sent to the REDIS buffer. Both modules
allow you to patch them, such that you can use e.g. the LaunchControl
to manipulate the properties of the signals in real time.

