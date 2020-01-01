addpath(genpath('~/matlab/liblsl'))

if ~exist('outlet')
  % instantiate the library
  disp('Loading library...');
  lib = lsl_loadlib();
  
  disp('Creating the marker stream info...');
  info = lsl_streaminfo(lib, 'experiment', 'markers', 1, 0, 'cf_string', '27652');
  
  disp('Opening an outlet...');
  outlet = lsl_outlet(info);
  
  % this is needed, otherwise the first marker is not sent/received
  pause(3)
end

%%

% send markers into the outlet
disp('Now transmitting data...');

disp('start');
outlet.push_sample({'start'});
pause(1)

for i=1:100
  disp('sync');
  outlet.push_sample({'sync'});
  pause(0.5)
end

disp('stop');
outlet.push_sample({'stop'});

% clear outlet lib