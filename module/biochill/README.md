# biochill module

The purpose of this module is to read breathing data from a FieldTrip buffer and compute a biofeedback score (range [0, 1]) which is send to Redis.
Details on the biofeedback processing are described in <link publication>.

The module is used in the following research project: https://www.nwo.nl/onderzoek-en-resultaten/onderzoeksprojecten/i/04/28504.html

# Requirements

Redis and a FieldTrip buffer should be running prior to starting this module.
