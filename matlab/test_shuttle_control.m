addpath d:/Github/eegsynth-matlab/
addpath d:/github/fieldtrip/
ft_defaults

clear all
midiOpen('output');

% >> midiOut('+', channel, notes, velocities)
midiOut('+', 1, 64, 50);
midiOut('-', 1, 64, 127);

while true
    for i = 0 : 128
        byte23 = typecast(uint16(i),'uint8');
        midiOut(uint8([225 byte23]))
        % midiOut(uint8([176 1 i ]))
        pause(0.0100);
    end
end

for ii = 1 : 10
    for i = 0 : 4096
        disp(i);
        midiOut(uint8([176 99 mod(i,127)]))
        midiOut(uint8([176 99 floor(i/127)]))
%         midiOut(uint8([224 floor(i/127) mod(i,127)]))
        pause(0.001);
    end
end

i = 1
 midiOut(uint8([225 floor(i/127) mod(i,127)]))

i = 64
 midiOut(uint8([225 floor(i/127) mod(i,127)]))
