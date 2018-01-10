%% use the audio card to play a sound

duration = 1; % second
f0 = 440; % Hz
fs = 22000; % Hz

a = 1;
while true
  fs = 22000;
  t = (1:duration*fs)/fs;
  s = a*sin(2*pi*f0*t); % .* tukeywin(length(t), 0.1)';
  s(length(s)/2+1:end) = 0;
  p = audioplayer(s, fs);
  playblocking(p)
end