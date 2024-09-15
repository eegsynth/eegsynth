from copy import deepcopy
from math import ceil, floor
from struct import pack, unpack
import calendar
import datetime
import numpy as np
import os
import re
import warnings

def padtrim(buf, num):
    num -= len(buf)
    if num>=0:
        # pad the input to the specified length
        retval = str(buf) + ' ' * num
    else:
        # trim the input to the specified length
        retval = buf[0:num]
    # convert output from char to bytes
    return retval.encode()

####################################################################################################
# the EDF header is represented as a tuple of (meas_info, chan_info)
# meas_info should have ['record_length', 'magic', 'hour', 'subject_id', 'recording_id', 'n_records', 'month', 'subtype', 'second', 'nchan', 'data_size', 'data_offset', 'lowpass', 'year', 'highpass', 'day', 'minute']
# chan_info should have ['physical_min', 'transducers', 'physical_max', 'digital_max', 'ch_names', 'n_samps', 'units', 'digital_min']
####################################################################################################

class EDFWriter():
    def __init__(self, fname=None):
        self.fname = None
        self.meas_info = None
        self.chan_info = None
        self.calibrate = None
        self.offset    = None
        self.n_records = 0
        if fname:
            self.open(fname)

    def open(self, fname):
        with open(fname, 'wb') as fid:
            assert(fid.tell() == 0)
        self.fname = fname

    def close(self):
        # it is still needed to update the number of records in the header
        # this requires copying the whole file content
        meas_info = self.meas_info
        chan_info = self.chan_info
        # update the n_records value in the file
        tempname = self.fname + '.bak'
        os.rename(self.fname, tempname)
        with open(tempname, 'rb') as fid1:
            assert(fid1.tell() == 0)
            with open(self.fname, 'wb') as fid2:
                assert(fid2.tell() == 0)
                fid2.write(fid1.read(236))
                fid1.read(8)                                    # skip this part
                fid2.write(padtrim(str(self.n_records), 8))     # but write this instead
                fid2.write(fid1.read(meas_info['data_offset'] - 236 - 8))
                blocksize = np.sum(chan_info['n_samps']) * meas_info['data_size']
                for block in range(self.n_records):
                    fid2.write(fid1.read(blocksize))
        os.remove(tempname)
        self.fname = None
        self.meas_info = None
        self.chan_info = None
        self.calibrate = None
        self.offset    = None
        self.n_records = 0
        return

    def writeHeader(self, header):
        meas_info = header[0]
        chan_info = header[1]
        meas_size = 256
        chan_size = 256 * meas_info['nchan']
        # note that the file is opened in binary mode, but the initial header is largely text
        # the padtrim function also converts the text to bytes
        with open(self.fname, 'wb') as fid:
            assert(fid.tell() == 0)

            # fill in the missing or incomplete information
            if not 'subject_id' in meas_info:
                meas_info['subject_id'] = ''
            if not 'recording_id' in meas_info:
                meas_info['recording_id'] = ''
            if not 'subtype' in meas_info:
                meas_info['subtype'] = 'edf'
            nchan = meas_info['nchan']
            if not 'ch_names' in chan_info or len(chan_info['ch_names'])<nchan:
                chan_info['ch_names'] = [str(i) for i in range(nchan)]
            if not 'transducers' in chan_info or len(chan_info['transducers'])<nchan:
                chan_info['transducers'] = ['' for i in range(nchan)]
            if not 'units' in chan_info or len(chan_info['units'])<nchan:
                chan_info['units'] = ['' for i in range(nchan)]

            if meas_info['subtype'] in ('24BIT', 'bdf'):
                meas_info['data_size'] = 3  # 24-bit (3 byte) integers
            else:
                meas_info['data_size'] = 2  # 16-bit (2 byte) integers

            fid.write(padtrim('0', 8))
            fid.write(padtrim(meas_info['subject_id'], 80))
            fid.write(padtrim(meas_info['recording_id'], 80))
            fid.write(padtrim('{:0>2d}.{:0>2d}.{:0>2d}'.format(meas_info['day'], meas_info['month'], meas_info['year']), 8))
            fid.write(padtrim('{:0>2d}.{:0>2d}.{:0>2d}'.format(meas_info['hour'], meas_info['minute'], meas_info['second']), 8))
            fid.write(padtrim(str(meas_size + chan_size), 8))
            fid.write(' '.encode() * 44)
            fid.write(padtrim(str(-1), 8))  # the final n_records should be inserted on byte 236
            fid.write(padtrim(str(meas_info['record_length']), 8))
            fid.write(padtrim(str(meas_info['nchan']), 4))

            # ensure that these are all np arrays rather than lists
            for key in ['physical_min', 'transducers', 'physical_max', 'digital_max', 'ch_names', 'n_samps', 'units', 'digital_min']:
                chan_info[key] = np.asarray(chan_info[key])

            for i in range(meas_info['nchan']):
                fid.write(padtrim(    chan_info['ch_names'][i], 16))
            for i in range(meas_info['nchan']):
                fid.write(padtrim(    chan_info['transducers'][i], 80))
            for i in range(meas_info['nchan']):
                fid.write(padtrim(    chan_info['units'][i], 8))
            for i in range(meas_info['nchan']):
                fid.write(padtrim(str(chan_info['physical_min'][i]), 8))
            for i in range(meas_info['nchan']):
                fid.write(padtrim(str(chan_info['physical_max'][i]), 8))
            for i in range(meas_info['nchan']):
                fid.write(padtrim(str(chan_info['digital_min'][i]), 8))
            for i in range(meas_info['nchan']):
                fid.write(padtrim(str(chan_info['digital_max'][i]), 8))
            for i in range(meas_info['nchan']):
                fid.write(' '.encode() * 80) # prefiltering
            for i in range(meas_info['nchan']):
                fid.write(padtrim(str(chan_info['n_samps'][i]), 8))
            for i in range(meas_info['nchan']):
                fid.write(' '.encode() * 32) # reserved
            meas_info['data_offset'] = fid.tell()

        self.meas_info = meas_info
        self.chan_info = chan_info
        self.calibrate = (chan_info['physical_max'] - chan_info['physical_min'])/(chan_info['digital_max'] - chan_info['digital_min']);
        self.offset    =  chan_info['physical_min'] - self.calibrate * chan_info['digital_min'];
        channels = list(range(meas_info['nchan']))
        for ch in channels:
            if self.calibrate[ch]<0:
              self.calibrate[ch] = 1;
              self.offset[ch]    = 0;

    def writeBlock(self, data):
        meas_info = self.meas_info
        chan_info = self.chan_info
        with open(self.fname, 'ab') as fid:
            assert(fid.tell() > 0)
            for i in range(meas_info['nchan']):
                raw = deepcopy(data[i])
                raw = np.asarray(raw, dtype=np.float64)

                assert(len(raw)==chan_info['n_samps'][i])
                if min(raw)<chan_info['physical_min'][i]:
                    warnings.warn('Value exceeds physical_min: ' + str(min(raw)) );
                if max(raw)>chan_info['physical_max'][i]:
                    warnings.warn('Value exceeds physical_max: '+ str(max(raw)));

                raw -= self.offset[i]  # FIXME I am not sure about the order of calibrate and offset
                raw /= self.calibrate[i]

                raw = np.asarray(raw, dtype=np.int16)
                buf = [pack('h', x) for x in raw]
                for val in buf:
                    fid.write(val)
            self.n_records += 1

####################################################################################################

class EDFReader():
    def __init__(self, fname=None):
        self.fname = None
        self.meas_info = None
        self.chan_info = None
        self.calibrate = None
        self.offset    = None
        if fname:
            self.open(fname)

    def open(self, fname):
        with open(fname, 'rb') as fid:
            assert(fid.tell() == 0)
        self.fname = fname
        self.readHeader()
        return self.meas_info, self.chan_info

    def close(self):
        self.fname = None
        self.meas_info = None
        self.chan_info = None
        self.calibrate = None
        self.offset    = None

    def readHeader(self):
        # the following is copied over from MNE-Python and subsequently modified
        # to more closely reflect the native EDF standard
        meas_info = {}
        chan_info = {}
        with open(self.fname, 'rb') as fid:
            assert(fid.tell() == 0)

            meas_info['magic']        = fid.read(8).strip().decode()
            meas_info['subject_id']   = fid.read(80).strip().decode()  # subject id
            meas_info['recording_id'] = fid.read(80).strip().decode()  # recording id

            day, month, year     = [int(x) for x in re.findall('(\d+)', fid.read(8).decode())]
            hour, minute, second = [int(x) for x in re.findall('(\d+)', fid.read(8).decode())]
            meas_info['day'] = day
            meas_info['month'] = month
            meas_info['year'] = year
            meas_info['hour'] = hour
            meas_info['minute'] = minute
            meas_info['second'] = second
            # date = datetime.datetime(year + 2000, month, day, hour, minute, sec)
            # meas_info['meas_date'] = calendar.timegm(date.utctimetuple())

            meas_info['data_offset'] = header_nbytes = int(fid.read(8).decode())

            subtype = fid.read(44).strip().decode()[:5]
            if len(subtype) > 0:
                meas_info['subtype'] = subtype
            else:
                meas_info['subtype'] = os.path.splitext(self.fname)[1][1:].lower()

            if meas_info['subtype'] in ('24BIT', 'bdf'):
                meas_info['data_size'] = 3  # 24-bit (3 byte) integers
            else:
                meas_info['data_size'] = 2  # 16-bit (2 byte) integers

            meas_info['n_records'] = n_records = int(fid.read(8).decode())

            # record length in seconds
            record_length = float(fid.read(8).decode())
            if record_length == 0:
                meas_info['record_length'] = record_length = 1.
                warnings.warn('Headermeas_information is incorrect for record length. '
                              'Default record length set to 1.')
            else:
                meas_info['record_length'] = record_length
            meas_info['nchan'] = nchan = int(fid.read(4).decode())

            channels = list(range(nchan))
            chan_info['ch_names']     = [fid.read(16).strip().decode() for ch in channels]
            chan_info['transducers']  = [fid.read(80).strip().decode() for ch in channels]
            chan_info['units']        = [fid.read(8).strip().decode() for ch in channels]
            chan_info['physical_min'] = physical_min = np.array([float(fid.read(8).decode()) for ch in channels])
            chan_info['physical_max'] = physical_max = np.array([float(fid.read(8).decode()) for ch in channels])
            chan_info['digital_min']  = digital_min  = np.array([float(fid.read(8).decode()) for ch in channels])
            chan_info['digital_max']  = digital_max  = np.array([float(fid.read(8).decode()) for ch in channels])

            prefiltering = [fid.read(80).strip().decode() for ch in channels][:-1]
            highpass     = np.ravel([re.findall('HP:\s+(\w+)', filt) for filt in prefiltering])
            lowpass      = np.ravel([re.findall('LP:\s+(\w+)', filt) for filt in prefiltering])
            high_pass_default = 0.
            if highpass.size == 0:
                meas_info['highpass'] = high_pass_default
            elif all(highpass):
                if highpass[0] == 'NaN':
                    meas_info['highpass'] = high_pass_default
                elif highpass[0] == 'DC':
                    meas_info['highpass'] = 0.
                else:
                    meas_info['highpass'] = float(highpass[0])
            else:
                meas_info['highpass'] = float(np.max(highpass))
                warnings.warn('Channels contain different highpass filters. '
                              'Highest filter setting will be stored.')

            if lowpass.size == 0:
                meas_info['lowpass'] = None
            elif all(lowpass):
                if lowpass[0] == 'NaN':
                    meas_info['lowpass'] = None
                else:
                    meas_info['lowpass'] = float(lowpass[0])
            else:
                meas_info['lowpass'] = float(np.min(lowpass))
                warnings.warn('%s' % ('Channels contain different lowpass filters.'
                                      ' Lowest filter setting will be stored.'))
            # number of samples per record
            chan_info['n_samps'] = n_samps = np.array([int(fid.read(8).decode()) for ch in channels])

            fid.read(32 *meas_info['nchan']).decode()  # reserved
            assert fid.tell() == header_nbytes

            if meas_info['n_records']==-1:
                # this happens if the n_records is not updated at the end of recording
                tot_samps = (os.path.getsize(self.fname)-meas_info['data_offset'])/meas_info['data_size']
                meas_info['n_records'] = int(tot_samps/sum(n_samps))

        self.calibrate = (chan_info['physical_max'] - chan_info['physical_min'])/(chan_info['digital_max'] - chan_info['digital_min']);
        self.offset    =  chan_info['physical_min'] - self.calibrate * chan_info['digital_min'];
        for ch in channels:
            if self.calibrate[ch]<0:
              self.calibrate[ch] = 1;
              self.offset[ch]    = 0;

        self.meas_info = meas_info
        self.chan_info = chan_info
        return (meas_info, chan_info)

    def readBlock(self, block):
        assert(block>=0)
        meas_info = self.meas_info
        chan_info = self.chan_info
        data = []
        with open(self.fname, 'rb') as fid:
            assert(fid.tell() == 0)
            blocksize = np.sum(chan_info['n_samps']) * meas_info['data_size']
            fid.seek(meas_info['data_offset'] + block * blocksize)
            for i in range(meas_info['nchan']):
                buf = fid.read(chan_info['n_samps'][i]*meas_info['data_size'])
                raw = np.asarray(unpack('<{}h'.format(chan_info['n_samps'][i]), buf), dtype=np.float32)
                raw *= self.calibrate[i]
                raw += self.offset[i]  # FIXME I am not sure about the order of calibrate and offset
                data.append(raw)
        return data

    def readSamples(self, channel, begsample, endsample):
        meas_info = self.meas_info
        chan_info = self.chan_info
        n_samps = chan_info['n_samps'][channel]
        begblock = int(floor((begsample) / n_samps))
        endblock = int(floor((endsample) / n_samps))
        data = self.readBlock(begblock)[channel]
        for block in range(begblock+1, endblock+1):
            data = np.append(data, self.readBlock(block)[channel])
        begsample -= begblock*n_samps
        endsample -= begblock*n_samps
        return data[begsample:(endsample+1)]

####################################################################################################
# the following are a number of helper functions to make the behaviour of this EDFReader
# class more similar to https://bitbucket.org/cleemesser/python-edf/
####################################################################################################

    def getSignalTextLabels(self):
        # convert from unicode to string
        return [str(x) for x in self.chan_info['ch_names']]

    def getNSignals(self):
        return self.meas_info['nchan']

    def getSignalFreqs(self):
        return self.chan_info['n_samps'] / self.meas_info['record_length']

    def getNSamples(self):
        return self.chan_info['n_samps'] * self.meas_info['n_records']

    def readSignal(self, chanindx):
        begsample = 0
        endsample = self.chan_info['n_samps'][chanindx] * self.meas_info['n_records'] - 1
        return self.readSamples(chanindx, begsample, endsample)

####################################################################################################

if False:
    file_in = EDFReader()
    file_in.open('/Users/roboos/day 01[10.03].edf')
    print(file_in.readSamples(0, 0, 0))
    print(file_in.readSamples(0, 0, 128))


if False:
    file_in = EDFReader()
    file_in.open('/Users/roboos/test_generator.edf')

    file_out = EDFWriter()
    file_out.open('/Users/roboos/test_generator copy.edf')

    header = file_in.readHeader()

    file_out.writeHeader(header)

    meas_info = header[0]
    for i in range(meas_info['n_records']):
        data = file_in.readBlock(i)
        file_out.writeBlock(data)

    file_in.close()
    file_out.close()
