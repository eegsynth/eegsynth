# Art-Net to Neopixel

This hardware module receives control signals over Art-Net (i.e. UDP packets) over a wireless connection. The Art-Net packets are used to drive an array of [Adafruit Neopixels](https://www.adafruit.com/category/168) or other LEDs that have a WS2812 controller in them.

We made multiple versions of this hardware, including versions that have the LEDs in a 12, 16 or 24 pixel ring (from Adafruit) or that have a long strip of LEDs (from Ebay).

The ESP8266 firmware allows you to configure whether you have RGBW or RGB LEDs and supports many different patterns.

This hardware works well with the *outputartnet* Python module.

The Arduino code for the firmware of this device can be found on [github](https://github.com/robertoostenveld/arduino/tree/master/esp8266_artnet_neopixel).
