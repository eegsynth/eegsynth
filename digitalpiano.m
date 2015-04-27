function piano

% make a GUI that resembles a piano

close all
h = figure;
set(h, 'MenuBar', 'none')
set(h, 'Name', 'Piano')
pos = get(h, 'Position');
pos(3) = 550;
pos(4) = 380;
set(h, 'Position', pos);

uicontrol('tag', '3_C',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_D',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_E',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_F',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_G',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_A',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_B',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Db', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Eb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Fb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Gb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Bb', 'callback', @callback, 'style', 'pushbutton', 'string', '');

uicontrol('tag', '4_C',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_D',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_E',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_F',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_G',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_A',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_B',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Db', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Eb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Fb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Gb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Bb', 'callback', @callback, 'style', 'pushbutton', 'string', '');

uicontrol('tag', '5_C',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_D',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_E',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_F',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_G',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_A',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_B',  'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Db', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Eb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Fb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Gb', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Bb', 'callback', @callback, 'style', 'pushbutton', 'string', '');

ft_uilayout(h, 'tag', '._[CDEFGAB]$', 'position', [0 0 020 100]);
ft_uilayout(h, 'tag', '._.b$',        'position', [0 0 020 70]);

ft_uilayout(h, 'tag', '[CDEFGAB]$', 'vpos', 150);
ft_uilayout(h, 'tag', 'b$',         'vpos', 180);

ft_uilayout(h, 'tag', 'C$', 'hpos', 020);
ft_uilayout(h, 'tag', 'D$', 'hpos', 040);
ft_uilayout(h, 'tag', 'E$', 'hpos', 060);
ft_uilayout(h, 'tag', 'F$', 'hpos', 080);
ft_uilayout(h, 'tag', 'G$', 'hpos', 100);
ft_uilayout(h, 'tag', 'A$', 'hpos', 120);
ft_uilayout(h, 'tag', 'B$', 'hpos', 140);

ft_uilayout(h, 'tag', 'Db$', 'hpos', 030);
ft_uilayout(h, 'tag', 'Eb$', 'hpos', 050);
ft_uilayout(h, 'tag', 'Fb$', 'hpos', 090);
ft_uilayout(h, 'tag', 'Gb$', 'hpos', 110);
ft_uilayout(h, 'tag', 'Bb$', 'hpos', 130);

ft_uilayout(h, 'tag', '^4', 'hshift', 140);
ft_uilayout(h, 'tag', '^5', 'hshift', 280);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function callback(h, event)
tag = get(h, 'tag');
disp(tag);

% I removed the first column to make the indexing consistent with the notation
% http://en.wikipedia.org/wiki/Scientific_pitch_notation

C  = [32.703 65.406 130.81 261.63 523.25 1046.5 2093.0 4186.0 8372.0 16744.0];
Db = [34.648 69.296 138.59 277.18 554.37 1108.7 2217.5 4434.9 8869.8 17739.7];
D  = [36.708 73.416 146.83 293.66 587.33 1174.7 2349.3 4698.6 9397.3 18794.5];
Eb = [38.891 77.782 155.56 311.13 622.25 1244.5 2489.0 4978.0 9956.1 19912.1];
E  = [41.203 82.407 164.81 329.63 659.26 1318.5 2637.0 5274.0 10548.1 21096.2];
F  = [43.654 87.307 174.61 349.23 698.46 1396.9 2793.8 5587.7 11175.3 22350.6];
Gb = [46.249 92.499 185.00 369.99 739.99 1480.0 2960.0 5919.9 11839.8 23679.6];
G  = [48.999 97.999 196.00 392.00 783.99 1568.0 3136.0 6271.9 12543.9 25087.7];
Ab = [51.913 103.83 207.65 415.30 830.61 1661.2 3322.4 6644.9 13289.8 26579.5];
A  = [55.000 110.00 220.00 440.00 880.00 1760.0 3520.0 7040.0 14080.0 28160.0];
Bb = [58.270 116.54 233.08 466.16 932.33 1864.7 3729.3 7458.6 14917.2 29834.5];
B  = [61.735 123.47 246.94 493.88 987.77 1975.5 3951.1 7902.1 15804.3 31608.5];

octave = str2num(tag(1));
note   = tag(3:end);

f = eval(sprintf('%s(%d)', note, octave));
fs = 22000;
t = (1:fs)/fs;
s = sin(2*pi*f*t);

p = audioplayer(s, fs);
playblocking(p);




