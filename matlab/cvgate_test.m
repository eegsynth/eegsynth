% a = cvgate('COM4:', 115200);

a.voltage = [];
a.gate    = [];


c = 0;
t = tic;
while true
  a.voltage(1) = 4095 * (0.4 + sin(0.5*2*pi*toc(t))/2);
%   a.voltage(2) = 5 * (0.3 + sin(0.5*2*pi*toc(t))/2);
%   a.voltage(3) = 5 * (0.2 + sin(0.5*2*pi*toc(t))/2);
%   a.voltage(4) = 5 * (0.1 + sin(0.5*2*pi*toc(t))/2);

  a.gate(1) = 1;

  update(a);
  c = c + 1;
  if mod(c, 100)==0
    % display the number of updates per second
    disp(c/toc(t));
  end
end