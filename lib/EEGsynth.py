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
      ay = lo-range/2
    else:
      ax = range/2-lo
      ay = 0.0

    if hi<range/2:
      bx = range
      by = range/2+hi
    else:
      bx = 1.5*range-hi
      by = range

    slope     = (by-ay)/(bx-ax)
    intercept = ay - ax*slope
    return (slope*xval + intercept)

print clip(limiter(  0, 63.5, 63.5, range=127))
print clip(limiter(127, 63.5, 63.5, range=127))

print clip(limiter(0, 0.5+0.1, 0.5, range=1))
print clip(limiter(1, 0.5, 0.5-0.1, range=1))
