import os
import sys
import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import mido
import OSC          # see https://trac.v2.nl/wiki/pyOSC

###################################################################################################
class midiwrapper():
    """Class to provide a generalized interface to MIDI interfaces on the local computer
    or to MIDI interfaces that are accessed on another computer over the network
    using the midiosc application. It only supports sending, not receiving.
    """

    def __init__(self, config):
        self.config = config
        self.outputport = None
        try:
            self.backend = config.get('midi', 'backend')
        except ConfigParser.NoOptionError:
            self.backend = 'mido'
        try:
            self.debug = config.getint('general', 'debug')
        except ConfigParser.NoOptionError:
            self.debug = 0

    def open_output(self):
        if self.backend == 'mido':
            if self.debug>0:
                print('------ OUTPUT ------')
                for port in mido.get_output_names():
                  print(port)
                print('-------------------------')
            try:
                self.outputport  = mido.open_output(self.config.get('midi', 'device'))
                print "Connected to MIDI output"
            except:
                print "Error: cannot connect to MIDI output"
                exit()

        elif self.backend == 'midiosc':
            try:
                self.outputport = OSC.OSCClient()
                self.outputport.connect((self.config.get('midi','hostname'), self.config.getint('midi','port')))
                print "Connected to OSC server"
            except:
                print "Error: cannot connect to OSC server"
                exit()

        else:
            raise NameError('unsupported backend: ' + self.backend)

    def send(self, mido_msg):
        if self.backend == 'mido':
            # send the message as is
            self.outputport.send(mido_msg)
        elif self.backend == 'midiosc':
            # convert the message to an OSC message that "midiosc" understands
            device_name = self.config.get('midi', 'device').replace(' ', '_')
            osc_address = "/midi/" + device_name + "/0"
            osc_msg = OSC.OSCMessage(osc_address)
            if mido_msg.type == 'control_change':
                osc_msg.append('controller_change')
                osc_msg.append(mido_msg.control)
                osc_msg.append(mido_msg.value)
            elif mido_msg.type == 'note_on':
                osc_msg.append('note_on')
                osc_msg.append(mido_msg.note)
                osc_msg.append(mido_msg.velocity)
            elif mido_msg.type == 'note_off':
                osc_msg.append('note_off')
                osc_msg.append(mido_msg.note)
                osc_msg.append(mido_msg.velocity)
            elif mido_msg.type == 'clock':
                osc_msg.append('timing_tick')
            elif mido_msg.type == 'pitchwheel':
                osc_msg.append('pitch_bend')
                osc_msg.append(mido_msg.pitch)
            else:
                raise NameError('unsupported message type')
            # send the OSC message, the receiving "midiosc" application will convert it back to MIDI
            self.outputport.send(osc_msg)
        else:
            raise NameError('unsupported backend: ' + self.backend)


####################################################################
# The formatting of the item in the ini file should be like this
#   item=1            this returns 1
#   item=key          get the value of the key from redis
# or if multiple is True
#   item=1-20         this returns [1,20]
#   item=1,2,3        this returns [1,2,3]
#   item=1,2,3,5-9    this returns [1,2,3,5,9], not [1,2,3,4,5,6,7,8,9]
#   item=key1,key2    get the value of key1 and key2 from redis
#   item=key1,5       get the value of key1 from redis
#   item=0,key2       get the value of key2 from redis
def getfloat(section, item, config, redis, multiple=False, default=None):

    if config.has_option(section, item):
        # get all items from the ini file, there might be one or multiple
        items = config.get(section, item)
        items = items.replace(' ', '')         # remove whitespace
        if items[0]!='-':
            items = items.replace('-', ',')    # replace minus separators by commas
        items = items.split(',')               # split on the commas
        val = [None]*len(items)

        for i,item in enumerate(items):
            # replace the item with the actual value
            try:
                val[i] = float(item)
            except ValueError:
                try:
                    val[i] = float(redis.get(item))
                except TypeError:
                    val[i] = default
    else:
        val = [default]

    if multiple:
        # return it as list
        return val
    else:
        # return a single value
        return val[0]

####################################################################
def getint(section, item, config, redis, multiple=False, default=None):

    if config.has_option(section, item):
        # get all items from the ini file, there might be one or multiple
        items = config.get(section, item)
        items = items.replace(' ', '')         # remove whitespace
        if items[0]!='-':
            items = items.replace('-', ',')    # replace minus separators by commas
        items = items.split(',')               # split on the commas
        val = [None]*len(items)

        for i,item in enumerate(items):
            # replace the item with the actual value
            try:
                val[i] = int(item)
            except ValueError:
                try:
                    val[i] = int(redis.get(item))
                except TypeError:
                    val[i] = default
    else:
        val = [default]

    if multiple:
        # return it as list
        return val
    else:
        # return a single value
        return val[0]

####################################################################
def rescale(xval, slope=None, offset=None):
    if hasattr(xval, "__iter__"):
        return [rescale(x, slope, offset) for x in xval]
    else:
        if slope is None:
            slope = 1
        if offset is None:
            offset = 0
        return float(slope)*xval + float(offset)

####################################################################
def clip(xval, lower=0.0, upper=127.0):
    if hasattr(xval, "__iter__"):
        return [clip(x, lower, upper) for x in xval]
    else:
        if xval<lower:
            return lower
        elif xval>upper:
            return upper
        else:
            return xval

####################################################################
def limiter(xval, lo=63.5, hi=63.5, range=127.0):
    if hasattr(xval, "__iter__"):
        return [limiter(x, lo, hi, range) for x in xval]
    else:
        xval  = float(xval)
        lo    = float(lo)
        hi    = float(hi)
        range = float(range)
        if lo>range/2:
          ax = 0.0
          ay = lo-(range+1)/2
        else:
          ax = (range+1)/2-lo
          ay = 0.0

        if hi<range/2:
          bx = (range+1)
          by = (range+1)/2+hi
        else:
          bx = 1.5*(range+1)-hi
          by = (range+1)

        if (bx-ax)==0:
            # threshold the value halfway
            yval = (xval>63.5)*range
        else:
            # map the value according to a linear transformation
            slope     = (by-ay)/(bx-ax)
            intercept = ay - ax*slope
            yval      = (slope*xval + intercept)

        if yval<0:
          yval = 0
        elif yval>range:
          yval = range

        return yval
