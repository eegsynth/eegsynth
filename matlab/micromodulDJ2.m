function micromodulDJ2(cfg)

% MICROMODULDJ2 creates a GUI that emulates the Faderfox Micromodul DJ2
%
% See http://www.faderfox.de/dj2.html

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
cfg.input    = ft_getopt(cfg, 'input', 'yes');    % yes, no
cfg.output   = ft_getopt(cfg, 'output', 'no');    % yes, no

% this table represents how the channel and note map onto a GUI tag
cfg.mapping = {
 '1_1_a',      8, 73 % not correct, testing only
 '1_2_a',      0,  0
 '1_3_a',      0,  0
 '2_1_a',      0,  0
 '2_2_a',      0,  0
 '2_3_a',      0,  0
 '1_4_c',      0,  0
 '1_5_b',      0,  0
 '1_6_b',      0,  0
 '1_7_b',      0,  0
 '2_5_b',      0,  0
 '2_6_b',      0,  0
 '2_7_b',      0,  0
 '3_1_a',      0,  0
 '3_7_b',      0,  0
 '4_1_a',      0,  0
 '4_2_a',      0,  0
 '4_6_b',      0,  0
 '4_7_b',      0,  0
 'slider_a',   8, 77 % not correct, testing only
 'slider_b',   8, 78 % not correct, testing only
 'slider_c',   8, 79 % not correct, testing only
 '5_1_low_a',  8, 49 % not correct, testing only
 '6_1_mid_a',  0,  0
 '7_1_hig_a',  0,  0
 '5_6_low_b',  0,  0
 '6_6_mid_b',  0,  0
 '7_6_hig_b',  0,  0
 '7_4_mix_c',  0,  0
 '8_1_gain_a', 0,  0
 '8_6_gain_b', 0,  0
  };

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
  t = timer('ExecutionMode', 'fixedRate', 'Period',  0.1, 'UserData', h, 'TimerFcn', @cb_timer);
  start(t);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function creategui(h)

figure(h);

pos = get(h, 'Position');
pos(1) = pos(1)+pos(3)/2-280/2;
pos(3) = 310;
pos(4) = 350;
set(h, 'Position', pos);
set(h, 'MenuBar', 'none')
set(h, 'Name', 'Micromodul DJ2')

uicontrol('tag', '1_1_a', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_2_a', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_3_a', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.2 0.2 0.5]);
uicontrol('tag', '2_1_a', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_2_a', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_3_a', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.2 0.2 0.5]);

uicontrol('tag', '1_4_c', 'style', 'pushbutton', 'string', '');

uicontrol('tag', '1_5_b', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_6_b', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_7_b', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.2 0.2 0.5]);
uicontrol('tag', '2_5_b', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_6_b', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_7_b', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.2 0.2 0.5]);

uicontrol('tag', '3_1_a', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.2 0.2 0.2]);
uicontrol('tag', '3_7_b', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.2 0.2 0.2]);

uicontrol('tag', '4_1_a', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.1 0.5 0.4]);
uicontrol('tag', '4_2_a', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.1 0.5 0.4]);
uicontrol('tag', '4_6_b', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.1 0.5 0.4]);
uicontrol('tag', '4_7_b', 'style', 'pushbutton', 'string', '', 'backgroundcolor', [0.1 0.5 0.4]);

uicontrol('tag', 'slider_a',   'style', 'slider',     'string', '');
uicontrol('tag', 'slider_b',   'style', 'slider',     'string', '');
uicontrol('tag', 'slider_c',   'style', 'slider',     'string', '');

uicontrol('tag', '5_1_low_a', 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '6_1_mid_a', 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '7_1_hig_a', 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '5_6_low_b', 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '6_6_mid_b', 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '7_6_hig_b', 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '7_4_mix_c', 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '8_1_gain_a', 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '8_6_gain_b', 'style', 'popupmenu',  'string', num2cell(1:127));

% all controls have the same callback function
ft_uilayout(h, 'tag', '^.*$', 'callback', @cb_interface);

ft_uilayout(h, 'style', 'popupmenu', 'value', 64);  % set the default value to the middle
ft_uilayout(h, 'style', 'slider',    'value', 0.5); % set the default value to the middle

% determine the generic size
ft_uilayout(h, 'style', 'pushbutton', 'position', [0 0 030 030]);
ft_uilayout(h, 'style', 'popupmenu',  'position', [0 0 070 030]);

% do the generic position on the grid
ft_uilayout(h, 'tag', '^._1_', 'hpos',  020);
ft_uilayout(h, 'tag', '^._2_', 'hpos',  060);
ft_uilayout(h, 'tag', '^._3_', 'hpos', 100);
ft_uilayout(h, 'tag', '^._4_', 'hpos', 140);
ft_uilayout(h, 'tag', '^._5_', 'hpos', 180);
ft_uilayout(h, 'tag', '^._6_', 'hpos', 220);
ft_uilayout(h, 'tag', '^._7_', 'hpos', 260);
ft_uilayout(h, 'tag', '^._8_', 'hpos', 300);

ft_uilayout(h, 'tag', '^1_', 'vpos',  020);
ft_uilayout(h, 'tag', '^2_', 'vpos',  060);
ft_uilayout(h, 'tag', '^3_', 'vpos', 100);
ft_uilayout(h, 'tag', '^4_', 'vpos', 140);
ft_uilayout(h, 'tag', '^5_', 'vpos', 180);
ft_uilayout(h, 'tag', '^6_', 'vpos', 220);
ft_uilayout(h, 'tag', '^7_', 'vpos', 260);
ft_uilayout(h, 'tag', '^8_', 'vpos', 300);
ft_uilayout(h, 'tag', '^9_', 'vpos', 340);

ft_uilayout(h, 'tag', 'slider_a',   'position', [140-35 140 030 110]);
ft_uilayout(h, 'tag', 'slider_b',   'position', [140+25 140 030 110]);
ft_uilayout(h, 'tag', 'slider_c',   'position', [110    100 095 030]);
ft_uilayout(h, 'tag', '7_4_mix_c',  'hshift', -15); 


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_interface(h, varargin)
cfg = guidata(h);
tag = get(h, 'tag');
disp(tag);

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
  tag     =          cfg.mapping(:,1);
  channel = cell2mat(cfg.mapping(:,2));
  note    = cell2mat(cfg.mapping(:,3));
end

for i=1:size(dat,1)
  sel = (channel==dat(i,1) & note==dat(i,2));
  if sum(sel)==1
    u = findobj('tag', tag{sel});
    switch lower(get(u, 'style'))
      case 'slider'
        set(u, 'value', dat(i,3)/127);
      case 'pushbutton'
        if dat(i,3)>0
          % pushed down
          set(u, 'backgroundcolor', [1 0 0]);
        else
          % released
          set(u, 'backgroundcolor', [0.9294 0.9294 0.9294]);
        end
      case 'popupmenu'
        set(u, 'value', dat(i,3));
    end % switch
  end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_cleanup(varargin)
delete(timerfindall)


