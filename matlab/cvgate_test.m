a = cvgate('/dev/tty.wchusbserial620', 115200);

a.voltage = [];
a.gate    = [];

c = 0;
t = tic;
while true
  a.voltage(1) = 5 * (0.4 + sin(0.5*2*pi*toc(t))/2);
%   a.voltage(2) = 5 * (0.3 + sin(0.5*2*pi*toc(t))/2);
%   a.voltage(3) = 5 * (0.2 + sin(0.5*2*pi*toc(t))/2);
%   a.voltage(4) = 5 * (0.1 + sin(0.5*2*pi*toc(t))/2);
  
  update(a);
  c = c + 1;
  if mod(c, 100)==0
    % display the number of updates per second
    disp(c/toc(t));
  end
end