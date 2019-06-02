# Inputcontrol module

This module presents a graphical user interface (GUI) with a configurable number of sliders, dials (knobs), buttons and text fields. It can be used as an alternative to a hardware MIDI controller such as the Novation LaunchControlXL. The values of the sliders and dials are sent as control signals to the Redis buffer. The button press and release events are sent as triggers to the Redis buffer.

For the buttons you can specify whether they should respond as push buttons (on/off) or as toggle buttons.

For the buttons you can specify whether they should respond as push buttons (on/off), slap buttons (not responding to off) or as toggle buttons. While push buttons are momentary, i.e. only "on" while you keep your them depressed, toggle buttons retain their state after you release them, pressing once more switches to the next state. The following options are supported, which are also represented using the color code of the LED:

- toggle1 buttons switch between on-off
- toggle2 buttons switch between on1-on2-off
- toggle3 buttons switch between on1-on2-on3-off
- toggle4 buttons switch between on1-on2-on3-on4-off

The content of the text field is interpreted as integer value.

![inputcontrol](./inputcontrol.png)

The resolution of the sliders, dials and buttons is the same as for MIDI controllers, i.e. in steps from 0 to 127. The scale and offset parameter are applied to prior to sending the output values to Redis.

## Specifying the layout

You can specify a simple layout with sliders on the left and buttons on the right by including a section '[slider]' and '[button]' in the ini file.

You can specify a more sophisticated layout by including multiple '[rowNUMBER]' and '[columnNUMBER]' sections in the ini file, where the number ranges from 1 to 16. Each row or column can include an arbitrary number of sliders, dials and/or buttons. The rows are placed under each other on the left side of the main window; the columns are placed next to each other on the right side of the main window.

```
            -  -  -  -
[ row 1 ]   c  c  c  c
[ row 2 ]   o  o  o  o
[ row 3 ]   l  l  l  l
[ row 4 ]   u  u  u  l
[ row 5 ]   m  m  m  m
[ row 6 ]   n  n  n  n
[ row 7 ]   1  2  3  4
            -  -  -  -
```

## LaunchControl XL and mini

Included are the `launchcontrolxl.ini` and `launchcontrolmini.ini` files, which result in a control interface that mimics the layout of the respective physical MIDI interface. The output values are written to Redis just as they would be using the `launchcontrol` module.

You can start them like this

    ./inputcontrol.py -i launchcontrolxl.ini

or

    ./inputcontrol.py -i launchcontrolmini.ini
