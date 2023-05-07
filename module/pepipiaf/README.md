# PepiPIAF module

The [PepiPIAF](https://www6.clermont.inrae.fr/piaf/Methodes-et-Modeles/PepiPIAF) is a biosensor to monitor perennial plants and trees. It consists of a box with a number of connectors for different sensors that can measure temperature, humidity, water level, light intensity, wind speed, and the slowly changing swelling and shrinking of the bark of the tree with a very precise displacement sensor.

The PepiPIAF is designed to be mounted on trees in a remote areas and to run battery-operated for a long time. It has two RF antenna's; one for the Sigfox/LORA protocol and another one for the 802.15.4 protocol, which relates to Zigbee. The Sigfox/LORA radio is used for long-range infrequent transmission (about every 10 minutes) of small amounts of measured data that is logged on an online cloud IoT dashboard. The Zigbee radio is used for a short-range connection to a computer with a USB dongle and allows for setting configuration parameters and for downloading the data that is stored in memory.

To allow for energy efficient operation, the frequency of the measurements can be configure between once every minute to once every 3 hours. The frequency of long-range transmission is limited by Sigfox/LORA, and cannot be more often than 144 times per 24 hours, corresponding to once every 10 minutes.

The short-range Zigbee radio wakes up every 30 seconds to transmit a "I am awake" message; followed by a short window during which it can receive commands from the computer. When the rapid-programming key is connected, it remains awake and transmits the message every second. While it is awake, the DataPIAF software on the Windows computer can interact with the PepiPIAF box. When initiating a connection with the PepiPIAF in the normal mode, it can take up to 30 seconds for it to wake up and respond.

This EEGsynth pepipiaf module is an alternative for the DataPIAF software. It connects every 30 seconds using the short-range Zigbee radio and requests the most recent data that was measured. In line with the EEGsynth design, that measurement is then sent to Redis, where other EEGsynth modules can read it pass it on as MIDI, OSC or DMX, allowing for example musical instruments or lighting systems to respond to the measurement of the tree.

This EEGsynth pepipiaf module is implemented in Python and runs on Windows, macOS and Linux. It is specifically designed to speed up the access to the measurements by using the short-range Zigbee radio. Other functionality of the DataPIAF software is not replicated and for configuring the PepiPIAF you still need the Windows software. It also does not interact with the Sigfox/LORA radio, nor with the online cloud IoT dashboard (grafana). The Python implementation is Open Source and might be useful when you are interested in studying the communication protocol.


## Settings

The `pepipiaf.ini` configuration file specifies the USB port to which the USB key is connected. That is probably `COM6` on windows and `/dev/tty.usbserial-AH6F9DJC` on macOS.


## Rapid-programming mode

By plugging in the rapid-programming key in the designated port, the rapid-programming mode is enabled and the PepiPIAF remains awake continuously. This allows for more rapid interaction during configuration and when probing the settings. However, the PepiPIAF is not taking any new measurements in rapid-programming mode.
