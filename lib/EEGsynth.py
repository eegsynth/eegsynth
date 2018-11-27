import ConfigParser # this is version 2.x specific, on version 3.x it is called "configparser" and has a different API
import mido
import os
import sys
import threading

try:
    # see https://trac.v2.nl/wiki/pyOSC
    # this one is a bit difficult to install on Raspbian
    import OSC
except:
    # this means that midiosc is not supported as midi backend
    print "Warning: pyOSC not found"

###################################################################################################
class waitfor(threading.Thread):
    """Class for patching triggers, it subscribes to a Redis channel, waits until it receives
    a message and executes a callback function.

    Use as
      thread = EEGsynth.waitfor(patch, channel, callback, options, lock=None)
      thread.start()
      # do something else
      thread.stop()
      thread.join()

    It provides the general methods
       thread.start()
       thread.stop()
       thread.join()
    and the following methods to interact with the options
       thread.set(key, val)
       thread.get(key)

    The callback function receives the channel name, value and options and should return
    the possibly updated options.
    """

    def __init__(self, patch, channels, callback, options, lock=None):
        threading.Thread.__init__(self)
        self.redis = patch.redis
        if isinstance(object, (list,)):
            self.channels = channels
        else:
            self.channels = [channels]
        self.callback = callback
        self.options = options
        self.running = True
        self.lock = lock

    def stop(self):
        self.running = False
        self.redis.publish('UNBLOCK', 1)

    def set(self, option, value):
        if self.lock == None:
            self.options[option] = value
        else:
            with self.lock:
                self.options[option] = value

    def get(self, option):
        if self.lock == None:
            return self.options[option]
        else:
            with self.lock:
                return self.options[option]

    def run(self):
        pubsub = self.redis.pubsub()
        for channel in self.channels:
            pubsub.subscribe(channel)
        pubsub.subscribe('UNBLOCK')
        while self.running:
            for item in pubsub.listen():
                if not self.running or not item['type'] == 'message':
                    break
                if item['channel'] in self.channels:
                    # only execute the callback for messages that are interesting, not to UNBLOCK
                    key = item['channel']
                    val = item['data']
                    if self.lock == None:
                        self.options = self.callback(key, val, self.options)
                    else:
                        with self.lock:
                            self.options = self.callback(key, val, self.options)

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
            device_name  = self.config.get('midi', 'device').replace(' ', '_')
            midi_channel = str(self.config.get('midi', 'channel'))
            osc_address  = "/midi/" + device_name + "/" + str(mido_msg.channel)
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


###################################################################################################
class patch():
    """Class to provide a generalized interface for patching modules using
    configuration files and Redis.

    The formatting of the item in the ini file should be like this
      item=1            this returns 1
      item=key          get the value of the key from redis
    or if multiple is True
      item=1-20         this returns [1,20]
      item=1,2,3        this returns [1,2,3]
      item=1,2,3,5-9    this returns [1,2,3,5,9], not [1,2,3,4,5,6,7,8,9]
      item=key1,key2    get the value of key1 and key2 from redis
      item=key1,5       get the value of key1 from redis
      item=0,key2       get the value of key2 from redis
    """

    def __init__(self, c, r):
        self.config = c
        self.redis  = r

    ####################################################################
    def getfloat(self, section, item, multiple=False, default=None):
        if self.config.has_option(section, item):
            # get all items from the ini file, there might be one or multiple
            items = self.config.get(section, item)

            if items == '':
                # construct an empty list
                items = []
            elif multiple:
                # convert the items to a list
                if items.find(",") > -1:
                    separator = ","
                elif items.find("-") > -1:
                    separator = "-"
                elif items.find("\t") > -1:
                    separator = "\t"
                else:
                    separator = " "
                items = squeeze(' ', items)        # remove excess whitespace
                items = squeeze(separator, items)  # remove double separators
                items = items.split(separator)     # split on the separator
            else:
                # make a list with a single item
                items = [items]

            # set the default
            if default != None:
                val = [float(default)] * len(items)
            else:
                val = [default] * len(items)

            for i,item in enumerate(items):
                try:
                    # if it resembles a value, use that
                    val[i] = float(item)
                except ValueError:
                    # if it is a string, get the value from Redis
                    try:
                        val[i] = float(self.redis.get(item))
                    except TypeError:
                        pass
        else:
            # the configuration file does not contain the item
            if multiple == True and default == None:
                return []
            elif multiple == True and default != None:
                return [float(x) for x in default]
            elif multiple == False and default == None:
                return None
            elif multiple == False and default != None:
                return float(default)

        if multiple:
            # return it as list
            return val
        else:
            # return a single value
            return val[0]


    ####################################################################
    def getint(self, section, item, multiple=False, default=None):
        assert multiple == False or default == None, "default value is not supported for multiple items"

        if self.config.has_option(section, item):
            # get all items from the ini file, there might be one or multiple
            items = self.config.get(section, item)

            if items == '':
                # construct an empty list
                items = []
            elif multiple:
                # convert the items to a list
                if items.find(",") > -1:
                    separator = ","
                elif items.find("-") > -1:
                    separator = "-"
                elif items.find("\t") > -1:
                    separator = "\t"
                else:
                    separator = " "
                items = squeeze(' ', items)        # remove excess whitespace
                items = squeeze(separator, items)  # remove double separators
                items = items.split(separator)     # split on the separator
            else:
                # make a list with a single item
                items = [items]

            # set the default
            if default != None:
                val = [int(default)] * len(items)
            else:
                val = [default] * len(items)

            for i,item in enumerate(items):
                try:
                    # if it resembles a value, use that
                    val[i] = int(item)
                except ValueError:
                    # if it is a string, get the value from Redis
                    try:
                        val[i] = int(round(float(self.redis.get(item))))
                    except TypeError:
                        pass
        else:
            # the configuration file does not contain the item
            if multiple == True and default == None:
                return  []
            elif multiple == True and default != None:
                return [float(x) for x in default]
            elif multiple == False and default == None:
                return None
            elif multiple == False and default != None:
                return float(default)

        if multiple:
            # return it as list
            return val
        else:
            # return a single value
            return val[0]

    ####################################################################
    def getstring(self, section, item, multiple=False):
        # get all items from the ini file, there might be one or multiple
        items = self.config.get(section, item)

        if multiple:
            # convert the items to a list
            if items.find(",") > -1:
                separator = ","
            elif items.find("-") > -1:
                separator = "-"
            elif items.find("\t") > -1:
                separator = "\t"
            else:
                separator = " "

            items = squeeze(separator, items)  # remove double separators
            items = items.split(separator)     # split on the separator

            # return it as list
            return items

        else:
            # return a single value
            return items

    ####################################################################
    def hasitem(self, section, item):
        # check whether an item is present in the ini file
        return self.config.has_option(section, item)

    ####################################################################
    def setvalue(self, item, val, debug=0, duration=0):
        self.redis.set(item, val)      # set it as control channel
        self.redis.publish(item, val)  # send it as trigger
        if debug:
            print item, '=', val
        if duration > 0:
            # switch off after a certain amount of time
            threading.Timer(duration, EEGynth.setstate, args=[item, 0.]).start()


####################################################################
def rescale(xval, slope=None, offset=None):
    if hasattr(xval, "__iter__"):
        return [rescale(x, slope, offset) for x in xval]
    else:
        if slope==None:
            slope = 1.0
        if offset==None:
            offset = 0.0
        return float(slope)*float(xval) + float(offset)

####################################################################
def limit(xval, lo=0.0, hi=127.0):
    if hasattr(xval, "__iter__"):
        return [limit(x, lo, hi) for x in xval]
    else:
        xval = float(xval)
        lo = float(lo)
        hi = float(hi)
        if xval < lo:
            return lo
        elif xval > hi:
            return hi
        else:
            return xval

####################################################################
def compress(xval, lo=63.5, hi=63.5, range=127.0):
    if hasattr(xval, "__iter__"):
        return [compress(x, lo, hi, range) for x in xval]
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

####################################################################
def normalizerange(xval, min, max):
    min = float(min)
    max = float(max)
    return (float(xval)-min)/(max-min)

####################################################################
def normalizestandard(xval, avg, std):
    avg = float(avg)
    std = float(std)
    return (float(xval)-avg)/std

####################################################################
def squeeze(char, string):
    while char*2 in string:
        string = string.replace(char*2, char)
    return string
