# OpenBCI

We frequently make use of [OpenBCI](https://openbci.com) boards to record EEG (brain), ECG (heart) or EMG (muscle) signals. Although the boards are commercially available, they are mainly aimed at hackers/makers, very flexible and not so user-friendly. This documentation contains a short summary of the configuration in our use cases.

# 8-channel Cyton for EMG or ECG

This is best implemented using a bipolar configuration.

These are the settings for 8 bipolar channels in the `openbci.ini` file:

    chan1 = x1060000X
    chan2 = x2060000X
    chan3 = x3060000X
    chan4 = x4060000X
    chan5 = x5060000X
    chan6 = x6060000X
    chan7 = x7060000X
    chan8 = x8060000X

With the header *pointing away from you*, the AGND is all the way on the right (both pins) and the bipolar channels start on the 2nd pin from the left.

# 8-channel Cyton for EEG

This is best implemented using a unipolar configuration in which all 8 channels are referenced to a common reference. For K channels EEG you have to attach K+2 electrodes to the head, which includes a ground and a reference electrode.

Using an 11x2 female header and a head sweatband you can construct a [head mounted](../hardware/headband) system that facilitates electrode placements and wireless recordings. Here we summarize the main features of that configuration.

These are the settings for 8 monopolar channels in the `openbci.ini` file. All channels are enabled for bias, although we usually use AGND for ground rather than BIAS.

    chan1 = x1060101X
    chan2 = x2160101X
    chan3 = x3160101X
    chan4 = x4160101X
    chan5 = x5160101X
    chan6 = x6160101X
    chan7 = x7160101X
    chan8 = x8060101X

The OpenBCI board comes with a right-angle 11x2 male header soldered to it. With the header *pointing away from you*, SRB is on the left, followed by N1P-N8P, BIAS and AGND on the right. The outer most pads on the PCB (AVSS on the left and AVDD on the right) are not connected to the header. SRB2 is on the side with the "P" pins and SRB1 is on the side with the "N" pins.

*Rumor has it that with this configuration, the ouput of the ADS1299 and of the Cyton board is inverted.*

We usually connect the 10 electrode leads to the SRB2 pin (the upper pin), P1-P8 (the upper pins) and one of the AGND pins, skipping the BIAS pin. This allows for a conventional common reference montage.

- pin SRB2 - white  - left mastoid (M1) or alternatively AFz
- pin P1   - grey   - electrode site O1
- pin P2   - purple - electrode site P3
- pin P3   - blue   - electrode site C3
- pin P4   - green  - electrode site F3
- pin P5   - yellow - electrode site F4
- pin P6   - orange - electrode site C4
- pin P7   - red    - electrode site P4
- pin P8   - brown  - electrode site O2
- pin AGND - black  - right mastoid (M2) or alternatively Fpz
