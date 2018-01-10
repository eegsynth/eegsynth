function yval = compress(xval, lo, hi, range)

if nargin<2 || isempty(lo)
  lo = 63.5;
end
if nargin<3 || isempty(hi)
  hi = 63.5;
end
if nargin<4 || isempty(range)
  range = 127;
end

if lo>range/2
  ax = 0.0;
  ay = lo-(range+1)/2;
else
  ax = (range+1)/2-lo;
  ay = 0.0;
end

if hi<range/2
  bx = (range+1);
  by = (range+1)/2+hi;
else
  bx = 1.5*(range+1)-hi;
  by = (range+1);
end

if (bx-ax)==0
  % threshold the value halfway
  yval = (xval>63.5)*range;
else
  % map the value according to a linear transformation
  slope     = (by-ay)/(bx-ax);
  intercept = ay - ax*slope;
  yval      = (slope*xval + intercept);
end

yval(yval<0) = 0;
yval(yval>range) = range;

