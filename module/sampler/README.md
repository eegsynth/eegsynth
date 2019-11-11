# Sampler

This module plays samples from file upon receiving a pub/sub trigger. All input files must be in WAV format with the same sampling rate, number of channels, and number of bits.

It is possible to adjust the playback volume, speed, onset, and offset. Furthermore, it is possible to apply a taper to avoid transient clicks at the edges. The speed is specified as value relative to the original speed. The onset is specified as value between 0 (begin) and 1 (end of the sample). The offset is specified as value between 1 (end) and 0 (begin of the sample). If the onset is greater than the offset, no sound will be played. The amount of tapering is specified as number between 0 (no tapering) and 1 (triangular taper over the whole duration).

## Converting a batch of files to WAV format

The command-line [sox](http://sox.sourceforge.net) application is very useful to convert a batch of files to a consistent file format and to normalize the volume.

```
for file in *.aif ; do
name=`basename $file .aif`
sox $file -b 16 $name.wav channels 1 norm
done
```

## Related software

[ReSlice](https://itunes.apple.com/us/app/reslice/id1187609531?mt=8) from [VirSyn](http://www.virsyn.de/) can slice and play audio samples using MIDI or touch interface.
 
