# breathrate module
#
# reads a filtered respiration channel from the FieldTrip buffer (low-pass
# filtered at 0.5 Hz) and provides an estimate of breathing rate, based on
# inhalation peaks; peaks are chosen over troughs since the former are more
# sharply defined than troughs in signals acquired with the Bitalino belt
# (link);
# peak detection is based on online averages of...
# ... breathing rate: throw out extrema that follow another extreme by half
# the period of the average rate
# ... peak prominence (link) : throw out extrema that have a prominen smaller
# than weight * average prominence;
# online averages are update according to D. Knuth; https: //dsp.stackexchange.com/ questions/811/determining-the-mean-and-standard-deviation-in-real-time
# outputs a 'breathrate' channel with a continuous value that contains the
# breathing rate in breath per minute