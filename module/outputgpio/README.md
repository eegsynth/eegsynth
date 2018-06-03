# Output GPIO Module

The purpose of this module is to transform control signals and published events
from Redis to the GPIO pins of a Raspberry Pi.

The naming of GPIO pins follows the WiringPi convention, which differs from the
Broadcom and the header pin numbers.

For the Raspberry Pi 2, the mapping between Broadcom, WiringPi and header pins
is as follows. Please note that the left side of this table corresponds to the
odd pins of the header and the right side of the table to the even pins.

| BCM | wPi |   Name  | Header | Header | Name    | wPi | BCM |
|-----|-----|---------|--------|--------|---------|-----|-----|
|     |     |    3.3v |    1   |   2    | 5v      |     |     |
|   2 |   8 |   SDA.1 |    3   |   4    | 5v      |     |     |
|   3 |   9 |   SCL.1 |    5   |   6    | 0v      |     |     |
|   4 |   7 | GPIO. 7 |    7   |   8    | TxD     | 15  | 14  |
|     |     |      0v |    9   |   10   | RxD     | 16  | 15  |
|  17 |   0 | GPIO. 0 |   11   |   12   | GPIO. 1 | 1   | 18  |
|  27 |   2 | GPIO. 2 |   13   |   14   | 0v      |     |     |
|  22 |   3 | GPIO. 3 |   15   |   16   | GPIO. 4 | 4   | 23  |
|     |     |    3.3v |   17   |   18   | GPIO. 5 | 5   | 24  |
|  10 |  12 |    MOSI |   19   |   20   | 0v      |     |     |
|   9 |  13 |    MISO |   21   |   22   | GPIO. 6 | 6   | 25  |
|  11 |  14 |    SCLK |   23   |   24   | CE0     | 10  | 8   |
|     |     |      0v |   25   |   26   | CE1     | 11  | 7   |
|   0 |  30 |   SDA.0 |   27   |   28   | SCL.0   | 31  | 1   |
|   5 |  21 | GPIO.21 |   29   |   30   | 0v      |     |     |
|   6 |  22 | GPIO.22 |   31   |   32   | GPIO.26 | 26  | 12  |
|  13 |  23 | GPIO.23 |   33   |   34   | 0v      |     |     |
|  19 |  24 | GPIO.24 |   35   |   36   | GPIO.27 | 27  | 16  |
|  26 |  25 | GPIO.25 |   37   |   38   | GPIO.28 | 28  | 20  |
|     |     |      0v |   39   |   40   | GPIO.29 | 29  | 21  |


# Requirements

Redis should be running.

This module should be started on a Raspberry Pi on which [WiringPi](http://wiringpi.com/download-and-install/) should be installed.
