# Sampler

This module plays samples from file upon receiving a pub/sub trigger. All input files must be in WAV format with the same sampling rate, number of channels, and number of bits.

## Converting a batch of files to a common format

The command-line [sox](http://sox.sourceforge.net) application is very useful to convert a batch of files to a consistent file format and to normalize the volume.

```
for file in *.aif ; do
name=`basename $file .aif`
sox $file -b 16 $name.wav channels 1 norm
done
```
