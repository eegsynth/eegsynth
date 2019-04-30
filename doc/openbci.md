# OpenBCI

We frequently make use of [OpenBCI](https://openbci.com) boards to record EEG (brain), ECG (heart) or EMG (muscle) signals. Although the boards are commercially available, they are mainly aimed at hackers/makers, very flexible and not so user-friendly. This documentation contains a short summary of the configuration we use.

## Hardware overview

The OpenBCI hardware comes in different varieties, and with different interfaces for data transfer. The main distinction is between the original 8-channel Cyton board and the 4-channel Ganglion board. The Cyton board can be extended to 16 channels using the Daisy module. Both the Cyton and Ganglion can be combined with the WiFi shield.

In principle this results in the following hardware/interface options

- Ganglion
  - interfaced with BLE
  - interfaced with WiFi shield
- Cyton
  - interfaced with dongle
  - interfaced with WiFi shield
- Cyton with Daisy
  - interfaced with dongle
  - interfaced with WiFi shield

The Cyton hardware uses an [RFduino module](https://www.sparkfun.com/products/retired/13219) that is built on the [Nordic nRF51822](https://www.nordicsemi.com/Products/Low-power-short-range-wireless/nRF51822), which supports both BLE and proprietary wireless applications. Although the Cyton board has a switch that can be toggled between BLE-OFF-PC, support for BLE has [not been implemented](https://docs.openbci.com/Hardware/04-Cyton_Bluetooth) in the firmware by the OpenBCI developers.

In principle the data format of the Daisy board is the same as for the Cyton, with the samples of the lower 8 channels interleaved with the samples of the higher 8 channels. I.e. the data comes in at 250 Hz, all odd samples are for channel 1-8, and the even samples are for channel 9-16.

## Programming language support

Besides the hardware, another aspect to consider is the support to configure the boards and to receive the data in different programming environments. The problem is that none of these covers the full hardware range.

- Programming (Java)
- Node.js (Javascript)
- Python
- C/C++

The OpenBCI_Gui is implemented in Programming (Java) and uses the OpenBCI Hub (which is implemented in Node.js) background application to interface with the hardware. That in principle makes the OpenBCI Hub an interesting target to interface with other software, but regretfully documentation is very limited.

The [OpenBCI_Python](https://github.com/OpenBCI/OpenBCI_C) interface is (so far) only fully implemented for the Cyton and Gandlion boards, but not for the WiFi shield. Furthermore, the Ganglion board is only supported on Linux due to the underlying BLE library not being compatible with Windows or macOS.

The [OpenBCI_C](https://github.com/OpenBCI/OpenBCI_C) implementation is very incomplete and does not deal with the Daisy Ganglion board, Daisy or WiFi shield. The FieldTrip project includes an [openbci2ft](http://www.fieldtriptoolbox.org/development/realtime/openbci/) implementation in ANSI C that is well tested (on macOS, Linux and Windows) and supports the Cyton and Daisy, but not the Ganglion nor WiFi shield.

# 8-channel Cyton for EMG or ECG

EMG, EOG or ECG is best implemented using a bipolar configuration.

These are the `openbci.ini` settings for 8 bipolar channels:

    chan1 = x1060000X
    chan2 = x2060000X
    chan3 = x3060000X
    chan4 = x4060000X
    chan5 = x5060000X
    chan6 = x6060000X
    chan7 = x7060000X
    chan8 = x8060000X

With the header _pointing away from you_, the AGND is all the way on the right (both pins) and the bipolar channels start on the 2nd pin from the left.

# 8-channel Cyton for EEG

EEG is best implemented using a unipolar configuration in which all 8 channels are referenced to a common reference. For N channels, you have to attach N+2 electrodes to the head, which includes a ground and a reference electrode.

Using an 11x2 female header and a head sweatband you can construct a [head mounted](../hardware/openbci_headband) system that facilitates electrode placements and wireless recordings. Here we summarize the main features of that configuration, in which we connect all electrode leads to the top row.

These are the `openbci.ini` settings for 8 monopolar channels using SRB1 as reference. All channels are enabled for bias, although we usually use AGND rather than BIAS.

    chan1 = x1060101X
    chan2 = x2160101X
    chan3 = x3160101X
    chan4 = x4160101X
    chan5 = x5160101X
    chan6 = x6160101X
    chan7 = x7160101X
    chan8 = x8060101X

_Rumor has it that with this configuration, the output of the ADS1299 and hence the Cyton board is inverted._

The OpenBCI board comes with a right-angle 11x2 male header soldered to it. With the header _pointing away from you_, SRB is on the left, followed by N1P-N8P, BIAS and AGND. The outer most pads on the PCB (AVSS on the left and AVDD on the right) are not connected to the header. SRB1 is on the upper side with the "P" pins and SRB2 is on the lower side with the "N" pins.

**Warning: in the [schematics](https://raw.githubusercontent.com/OpenBCI/Docs/master/assets/images/OBCI_V3_32bit-Schematic.jpg) of the OpenBCI cyton board the SRB1 and SBB2 labels are swapped; in the TI [ADS1299 datasheet](http://www.ti.com/lit/ds/symlink/ads1299.pdf) you can see that SRB1 is pin 17 on the corner, and hence following the [PCB layout](https://raw.githubusercontent.com/OpenBCI/Docs/master/assets/images/OBCI_32bit_layerTop.jpg) connected to the top pin of the double cyton header.**
