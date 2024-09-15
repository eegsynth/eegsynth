# PepiPlayback module

The [PepiPIAF](https://www6.clermont.inrae.fr/piaf/Methodes-et-Modeles/PepiPIAF) is a biosensor to monitor perennial plants and trees. It consists of a box with a number of connectors for different sensors that can measure temperature, humidity, water level, light intensity, wind speed, and the slowly changing swelling and shrinking of the bark of the tree with a very precise displacement sensor.

EEGsynth includes a `pepipiaf` module that reads the data in real time and sends it to redis. The `pepipiaf` module also writes the values to a CSV file. This `pepiplayback` module reads the CSV file and plays it back according to the original speed, or optionally speeding it up with a certain factor.
