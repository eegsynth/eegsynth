# Frequently Asked Questions

## I receive a "Bad file descriptor" error

If openbci2ft gives this error trying to access /dev/ttyUSB0, it
is because the device is readonly for a normal user. The problem
does not apply if you run openbci2ft as root, i.e. with sudo.

## How can I improve the timing of the OpenBCI data stream

On http://ebrain.io/openbci-ftdi-driver/ and http://www.ftdichip.com/Support/Documents/AppNotes/AN232B-04_DataLatencyFlow.pdf
you can find suggestions to improve timing for the FTDI driver that is used with the OpenBCI RF dongle.

## I receive a "OSError: dlopen(libportmidi.dylib, 6): image not found" error

This error can happen on OS X El Captain, even if you have installed portmidi correctly using macports or homebrew. The problem is that python cannot load custom libraries due to the [system integrity protection](https://en.wikipedia.org/wiki/System_Integrity_Protection) feature introduced with El Captain.

To work around this you can [disable system integrity protection](
http://www.howtogeek.com/230424/how-to-disable-system-integrity-protection-on-a-mac-and-why-you-shouldnt/).

If you run into this on older versions of OS X, it is probably due to libmacports.dylib not being installed, or due to an incorrect setting of DYLD_LIBRARY_PATH.

## Localhost not recognized on OS X

In some OS X installations the name "localhost" does not refer to 127.0.0.1 as it should. This can be fixed by adding the following line to /etc/hosts

```
127.0.0.1        localhost
```
