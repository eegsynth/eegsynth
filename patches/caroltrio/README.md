# Starting all modules


The correct way to start the modules is

-  redis.sh you might have this running in the background
-  buffer.sh this starts two buffers
-  inputmidi.sh an alternative is to use redis-cli, see below
-  openbci2ft.sh
-  audio2ft.sh
-  preprocessing.sh
-  plotsignal.sh
-  plotspectral.sh
-  recordsignal_edf.sh
-  recordsignal_wav.sh

Instead of using the openbci2ft and the audio2ft modules in the recording
session, you can start the following modules in the playback session.

-  playbacksignal_edf.sh
-  playbacksignal_wav.sh
-  outputaudio.sh

The openbci2ft and the audio2ft modules MUST be switched of once these are
running. Furthermore, the two playback modules will respond to a midi note
to enable playing, to pause and to rewind.

# Enable/disable recording and playback

Since the inputmidi module does not support the latching of buttons like the
launchcontrol module (i.e. a button switches to on when pressed once, and
switches to off when pressed a sedonc time), and since I do not want to keep the
button pressed all the time, I will use redis-cli instead to write the control
values directly to the Redis buffer.

The actual midi notes correspond to the row of buttons on the small Launch
Control device.

redis-cli set midi.note009 1  # for record on
redis-cli set midi.note009 0  # for record off
redis-cli set midi.note010 1  # for playback on
redis-cli set midi.note010 0  # for playback off
redis-cli set midi.note011 1  # for playback pause on
redis-cli set midi.note011 0  # for playback pause off
redis-cli set midi.note012 1  # for playback rewind on
redis-cli set midi.note012 0  # for playback rewind off

# Schematic representation

![image](patch.png)
