# Frequently Asked Questions

## Communication with the buffer on localhost is slow on Linux

When you try to transmit a lot of samples on the localhost "loopback" device on Linux, you may notice that the performance is worse than transmitting them over the network. This is due to the protocol used, which involves a request/response pair. When sending data, the request (PUT_DAT) is large and the response (PUT_OK) is small. When receiving data, the request (GET_DAT) is small and the response (GET_OK) is large. Linux will automatically queue the small messages and pack them together in a single network package to reduce overhead. The (maximum) size of a network package is the [MTU](https://en.wikipedia.org/wiki/Maximum_transmission_unit).

The default MTU size for the loopback interface on Linux has been increased over time, i.e. compared to Linux releases from 10 years ago. For Debian Jessie and Stretch the default MTU for the loopback device is 65536. The consequence of this large MTU size is that transfer of the small messages between buffer client and server is delayed, limiting the performance.

You can change the MTU size with

    sudo ifconfig lo mtu 1500

The value of 1500 bytes is default on the other (networked) interfaces, and happens to be the upper limit for network routers that do not support [jumbo frames](https://en.wikipedia.org/wiki/Jumbo_frame). It is a value that works well for local data transfer, allowing for a smooth transfer of approximately 1.000.000 samples per second, corresponding to for example 1 channel at 1MHz, 20 channels at 48KHz (audio) or 1000 channels at 1KHz.

## I receive a "Bad file descriptor" error

If openbci2ft gives this error trying to access /dev/ttyUSB0, it is because the device is readonly for a normal user. The problem does not apply if you run openbci2ft as root, i.e. with sudo.

## How can I identify my MIDI devices?

Most EEGsynth modules that interface with MIDI will print all available MIDI input and output devices upon startup. On http://tedfelix.com/linux/linux-midi.html you can find a great page with details on Linux command line tools to explore soundcard and MIDI devices. On macOS you can use the "Audio MIDI Setup.app" application.

## How can I improve the timing of the OpenBCI data stream?

On http://ebrain.io/openbci-ftdi-driver/ and http://www.ftdichip.com/Support/Documents/AppNotes/AN232B-04_DataLatencyFlow.pdf
you can find suggestions to improve timing for the FTDI driver that is used with the OpenBCI RF dongle.

## I receive a "OSError: dlopen(libportmidi.dylib, 6): image not found" error

This error can happen on OS X El Captain, even if you have installed portmidi correctly using macports or homebrew. The problem is that python cannot load custom libraries due to the [system integrity protection](https://en.wikipedia.org/wiki/System_Integrity_Protection) feature introduced with El Captain.

To work around this you can [disable system integrity protection](
http://www.howtogeek.com/230424/how-to-disable-system-integrity-protection-on-a-mac-and-why-you-shouldnt/).

If you run into this on older versions of macOS, it is probably due to libmacports.dylib not being installed, or due to an incorrect setting of DYLD_LIBRARY_PATH.

## Localhost not recognized on macOS

In some macOS installations the name "localhost" does not refer to 127.0.0.1 as it should. This can be fixed by adding the following line to /etc/hosts

```
127.0.0.1        localhost
```
