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

    if multiple:
        # return it as list
        return val
    else:
        # return a single value
        return val[0]

####################################################################
def getint(section, item, config, redis, multiple=False, default=None):

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

    if multiple:
        # return it as list
        return val
    else:
        # return a single value
        return val[0]

####################################################################
def rescale(xval, slope=1, offset=0):
    return float(slope)*xval + float(offset)

####################################################################
def clip(xval, lower=0.0, upper=127.0):
    if xval<lower:
        return lower
    elif xval>upper:
        return upper
    else:
        return xval

####################################################################
def limiter(xval, lo=63.5, hi=63.5, range=127.0):
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
