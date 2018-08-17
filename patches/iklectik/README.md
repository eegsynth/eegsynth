This is the patch used for the Hemispherics performance at Iklectik.
See this [link](http://www.eegsynth.org/?p=1432) for details.

We recorded EEG from two subjects. One of the EEGsynth patches was running on a
Dell laptop running Linux, the other on a MacBook Pro running macOS. Since the
openbci2ft application on the MacBook was rather choppy (probably due to
suboptimal USB buffer settings), we connected the OpenBCI USB dongle to a
Raspberry Pi running openbci2ft. The data was streamed immediately to the
buffer running on the MacBook.
