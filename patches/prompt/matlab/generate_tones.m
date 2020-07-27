fsample = 48000;
duration = 0.2; % in seconds

time = 0 : 1/fsample : duration;

frequency = 880;
sound = sin(2*pi*frequency*time);
audiowrite('start.wav', sound, fsample);

frequency = 440;
sound = sin(2*pi*frequency*time);
audiowrite('sync.wav', sound, fsample);

frequency = 1760;
sound = sin(2*pi*frequency*time);
audiowrite('stop.wav', sound, fsample);

% p = audioplayer(sound, fsample);
% p.play