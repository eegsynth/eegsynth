function digitalpiano(cfg)

% DIGITALPIANO create a GUI with a digital piano that plays the notes using MIDI or
% using the soundcard.
%
% This interface has been designed for and tested with the Yamaha P95
% digital piano, but should also work with any other 88-key MIDI controller.

% Copyright (C) 2015, Robert Oostenveld
%
% This file is part of EEGSYNTH, see https://github.com/oostenveld/eegsynth-matlab
% for the documentation and details.
%
%    EEGSYNTH is free software: you can redistribute it and/or modify
%    it under the terms of the GNU General Public License as published by
%    the Free Software Foundation, either version 3 of the License, or
%    (at your option) any later version.
%
%    EEGSYNTH is distributed in the hope that it will be useful,
%    but WITHOUT ANY WARRANTY; without even the implied warranty of
%    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%    GNU General Public License for more details.
%
%    You should have received a copy of the GNU General Public License
%    along with EEGSYNTH. If not, see <http://www.gnu.org/licenses/>.

if isempty(which('ft_defaults'))
  error('this function requires that the FieldTrip toolbox is installed, see http://www.fieldtriptoolbox.org');
else
  % ensure that the FieldTrip path is properly set up
  ft_defaults
end

if nargin<1
  cfg = [];
end

% get the options, use defaults where needed
cfg.channel   = ft_getopt(cfg, 'channel', 1);
cfg.velocity  = ft_getopt(cfg, 'velocity', 64);
cfg.input     = ft_getopt(cfg, 'input', 'yes');
cfg.output    = ft_getopt(cfg, 'output', 'yes');
cfg.playsound = ft_getopt(cfg, 'playsound', 'no');

% this table contains the UI tag, channel and note
cfg.mapping = cell(120,3);

for i=1:11
  % see http://en.wikipedia.org/wiki/Scientific_pitch_notation
  cfg.mapping((i-1)*12+1,  :) = {sprintf('%d_C' , i-1), 0, i*12+0};
  cfg.mapping((i-1)*12+2,  :) = {sprintf('%d_Db', i-1), 0, i*12+1};
  cfg.mapping((i-1)*12+3,  :) = {sprintf('%d_D' , i-1), 0, i*12+2};
  cfg.mapping((i-1)*12+4,  :) = {sprintf('%d_Eb', i-1), 0, i*12+3};
  cfg.mapping((i-1)*12+5,  :) = {sprintf('%d_E' , i-1), 0, i*12+4};
  cfg.mapping((i-1)*12+6,  :) = {sprintf('%d_F' , i-1), 0, i*12+5};
  cfg.mapping((i-1)*12+7,  :) = {sprintf('%d_Gb', i-1), 0, i*12+6};
  cfg.mapping((i-1)*12+8,  :) = {sprintf('%d_G' , i-1), 0, i*12+7};
  cfg.mapping((i-1)*12+9,  :) = {sprintf('%d_Ab', i-1), 0, i*12+8};
  cfg.mapping((i-1)*12+10, :) = {sprintf('%d_A' , i-1), 0, i*12+9};
  cfg.mapping((i-1)*12+11, :) = {sprintf('%d_Bb', i-1), 0, i*12+10};
  cfg.mapping((i-1)*12+12, :) = {sprintf('%d_B' , i-1), 0, i*12+11};
end

close all

if strcmp(cfg.input, 'yes')
  midiOpen('input');
end

if strcmp(cfg.output, 'yes')
  midiOpen('output');
end

h = figure;
guidata(h, cfg);
set(h, 'DeleteFcn', @cb_cleanup);
creategui(h);

if strcmp(cfg.input, 'yes')
  t = timer('ExecutionMode', 'fixedRate', 'Period', 0.1, 'UserData', h, 'TimerFcn', @cb_timer);
  start(t);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function creategui(h)

figure(h);
pos = get(h, 'Position');
pos(1) = pos(1)+pos(3)/2-1080/2;
pos(3) = 1080;
pos(4) = 140;
set(h, 'Position', pos);
set(h, 'MenuBar', 'none')
set(h, 'Name', 'Piano')

uicontrol('tag', '0_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '1_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '2_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '3_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '4_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '5_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '6_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '7_C',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_D',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_E',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_F',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_G',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_A',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_B',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_Db', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_Eb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_Gb', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_Ab', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_Bb', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '8_C',  'style', 'pushbutton', 'string', '');

% all controls have the same callback function
ft_uilayout(h, 'tag', '^.*$', 'callback', @cb_interface);

ft_uilayout(h, 'tag', '._[CDEFGAB]$', 'position', [0 0 020 100]);
ft_uilayout(h, 'tag', '._.b$',        'position', [0 0 014 070]);

ft_uilayout(h, 'tag', '[CDEFGAB]$', 'BackgroundColor', 'w'); % white
ft_uilayout(h, 'tag', 'b$',         'BackgroundColor', 'k'); % black

ft_uilayout(h, 'tag', '[CDEFGAB]$', 'vpos', 020);
ft_uilayout(h, 'tag', 'b$',         'vpos', 050);

ft_uilayout(h, 'tag', 'C$', 'hpos', 020);
ft_uilayout(h, 'tag', 'D$', 'hpos', 040);
ft_uilayout(h, 'tag', 'E$', 'hpos', 060);
ft_uilayout(h, 'tag', 'F$', 'hpos', 080);
ft_uilayout(h, 'tag', 'G$', 'hpos', 100);
ft_uilayout(h, 'tag', 'A$', 'hpos', 120);
ft_uilayout(h, 'tag', 'B$', 'hpos', 140);

ft_uilayout(h, 'tag', 'Db$', 'hpos', 033);
ft_uilayout(h, 'tag', 'Eb$', 'hpos', 053);
ft_uilayout(h, 'tag', 'Gb$', 'hpos', 093);
ft_uilayout(h, 'tag', 'Ab$', 'hpos', 113);
ft_uilayout(h, 'tag', 'Bb$', 'hpos', 133);

ft_uilayout(h, 'tag', '^0', 'hshift', 40-1*140);
ft_uilayout(h, 'tag', '^1', 'hshift', 40+0*140);
ft_uilayout(h, 'tag', '^2', 'hshift', 40+1*140);
ft_uilayout(h, 'tag', '^3', 'hshift', 40+2*140);
ft_uilayout(h, 'tag', '^4', 'hshift', 40+3*140);
ft_uilayout(h, 'tag', '^5', 'hshift', 40+4*140);
ft_uilayout(h, 'tag', '^6', 'hshift', 40+5*140);
ft_uilayout(h, 'tag', '^7', 'hshift', 40+6*140);
ft_uilayout(h, 'tag', '^8', 'hshift', 40+7*140);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_interface(h, varargin)
cfg = guidata(h);
tag = get(h, 'tag');
disp(tag);

% parse the tag (e.g. 4_C) into the octave and note
octave = str2double(tag(1));
note   = tag(3:end);

if strcmp(cfg.playsound, 'yes')
  % the first column is octave 0 according to http://en.wikipedia.org/wiki/Scientific_pitch_notation
  frequency.C  = [16.352 32.703 65.406 130.81 261.63 523.25 1046.5 2093.0 4186.0  8372.0 16744.0];
  frequency.Db = [17.324 34.648 69.296 138.59 277.18 554.37 1108.7 2217.5 4434.9  8869.8 17739.7];
  frequency.D  = [18.354 36.708 73.416 146.83 293.66 587.33 1174.7 2349.3 4698.6  9397.3 18794.5];
  frequency.Eb = [19.445 38.891 77.782 155.56 311.13 622.25 1244.5 2489.0 4978.0  9956.1 19912.1];
  frequency.E  = [20.602 41.203 82.407 164.81 329.63 659.26 1318.5 2637.0 5274.0 10548.1 21096.2];
  frequency.F  = [21.827 43.654 87.307 174.61 349.23 698.46 1396.9 2793.8 5587.7 11175.3 22350.6];
  frequency.Gb = [23.125 46.249 92.499 185.00 369.99 739.99 1480.0 2960.0 5919.9 11839.8 23679.6];
  frequency.G  = [24.500 48.999 97.999 196.00 392.00 783.99 1568.0 3136.0 6271.9 12543.9 25087.7];
  frequency.Ab = [25.957 51.913 103.83 207.65 415.30 830.61 1661.2 3322.4 6644.9 13289.8 26579.5];
  frequency.A  = [27.500 55.000 110.00 220.00 440.00 880.00 1760.0 3520.0 7040.0 14080.0 28160.0];
  frequency.Bb = [29.135 58.270 116.54 233.08 466.16 932.33 1864.7 3729.3 7458.6 14917.2 29834.5];
  frequency.B  = [30.868 61.735 123.47 246.94 493.88 987.77 1975.5 3951.1 7902.1 15804.3 31608.5];
  
  fs = 22000;
  t = (1:0.5*fs)/fs;
  f = frequency.(note);
  f = f(octave-1);
  s = sin(2*pi*f*t) .* tukeywin(length(t), 0.1)';
  p = audioplayer(s, fs);
  playblocking(p);
end

if strcmp(cfg.output, 'yes')
  midi.C  = (1:11)*12 + 0;
  midi.Db = (1:11)*12 + 1;
  midi.D  = (1:11)*12 + 2;
  midi.Eb = (1:11)*12 + 3;
  midi.E  = (1:11)*12 + 4;
  midi.F  = (1:11)*12 + 5;
  midi.Gb = (1:11)*12 + 6;
  midi.G  = (1:11)*12 + 7;
  midi.Ab = (1:11)*12 + 8;
  midi.A  = (1:11)*12 + 9;
  midi.Bb = (1:11)*12 + 10;
  midi.B  = (1:11)*12 + 11;
  
  n = midi.(note);
  n = n(octave+1);
  midiOut('+', cfg.channel, n, cfg.velocity)
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_timer(t, varargin)
persistent tag channel note

dat = midiIn('G');

if isempty(dat)
  return
end

for i=1:size(dat,1)
  fprintf('input: channel %3d, note %3d, velocity %3d, timestamp %d\n', dat(i,1), dat(i,2), dat(i,3), dat(i,4));
end

h   = get(t, 'UserData');
cfg = guidata(h);

if isempty(tag)
  % this is only needed once
  tag     = cfg.mapping(:,1);
  channel = cell2mat(cfg.mapping(:,2));
  note    = cell2mat(cfg.mapping(:,3));
end

for i=1:size(dat,1)
  sel = (channel==dat(i,1) & note==dat(i,2));
  if sum(sel)==1
    u = findobj(h, 'tag', tag{sel});
    if numel(u)==1
      switch lower(get(u, 'style'))
        case 'pushbutton'
          if dat(i,3)>0
            % pushed down
            set(u, 'backgroundcolor', [1 0 0]);
          else
            % released, switch back to white or black
            tmp = get(u, 'tag');
            if tmp(end)=='b'
              set(u, 'backgroundcolor', [0 0 0]);
            else
              set(u, 'backgroundcolor', [1 1 1]);
            end
          end
      end % switch
    else
      disp(dat);
    end
  end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_cleanup(varargin)
delete(timerfindall)
