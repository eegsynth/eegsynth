function launchcontrolXL(cfg)

% LAUNCHCONTROLXL creates a GUI that emulates the Novation LaunchControl XL
%
% See http://global.novationmusic.com/launch/launch-control-xl

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
  '1_control',       8, 73
  '1_focus',         8, 41
  '1_slide',         8, 77
  '1_pan',           8, 49
  '1_sendB',         8, 13
  '1_sendA',         8, 29
  '2_control',       8, 73+1
  '2_focus',         8, 41+1
  '2_slide',         8, 77+1
  '2_pan',           8, 49+1
  '2_sendB',         8, 13+1
  '2_sendA',         8, 29+1
  '3_control',       8, 73+2
  '3_focus',         8, 41+2
  '3_slide',         8, 77+2
  '3_pan',           8, 49+2
  '3_sendB',         8, 13+2
  '3_sendA',         8, 29+2
  '4_control',       8, 73+3
  '4_focus',         8, 41+3
  '4_slide',         8, 77+3
  '4_pan',           8, 49+3
  '4_sendB',         8, 13+3
  '4_sendA',         8, 29+3
  '5_control',       8, 89
  '5_focus',         8, 57
  '5_slide',         8, 81
  '5_pan',           8, 53
  '5_sendB',         8, 17
  '5_sendA',         8, 33
  '6_control',       8, 89+1
  '6_focus',         8, 57+1
  '6_slide',         8, 81+1
  '6_pan',           8, 53+1
  '6_sendB',         8, 17+1
  '6_sendA',         8, 33+1
  '7_control',       8, 89+2
  '7_focus',         8, 57+2
  '7_slide',         8, 81+2
  '7_pan',           8, 53+2
  '7_sendB',         8, 17+2
  '7_sendA',         8, 33+2
  '8_control',       8, 89+3
  '8_focus',         8, 57+3
  '8_slide',         8, 81+3
  '8_pan',           8, 53+3
  '8_sendB',         8, 17+3
  '8_sendA',         8, 33+3
  '0_record',        8, 0
  '0_solo',          8, 0
  '0_mute',          8, 0
  '0_device',        8, 105
  '0_trackL',        8, 0
  '0_trackR',        8, 0
  '0_sendU',         8, 0
  '0_sendD',         8, 0
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
  t = timer('ExecutionMode', 'fixedRate', 'Period', 0.1, 'UserData', h, 'TimerFcn', @cb_timer);
  start(t);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function creategui(h)

figure(h);

pos = get(h, 'Position');
pos(3) = 580;
pos(4) = 380;
set(h, 'Position', pos);
set(h, 'MenuBar', 'none')
set(h, 'Name', 'LaunchControl XL')

uicontrol('tag', '1_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '1_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '1_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '1_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '2_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '2_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '2_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '2_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '3_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '3_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '3_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '3_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '4_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '4_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '4_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '4_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '5_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '5_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '5_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '5_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '6_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '6_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '6_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '6_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '7_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '7_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '7_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '7_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '8_control', 'style', 'pushbutton', 'string', '');
uicontrol('tag', '8_focus',   'style', 'pushbutton', 'string', '');
uicontrol('tag', '8_slide',   'style', 'slider',     'string', '');
uicontrol('tag', '8_pan',     'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '8_sendB',   'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '8_sendA',   'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '0_record',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_solo',    'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_mute',    'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_device',  'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_trackL',  'style', 'pushbutton', 'string', '<');
uicontrol('tag', '0_trackR',  'style', 'pushbutton', 'string', '>');
uicontrol('tag', '0_sendU',   'style', 'pushbutton', 'string', '^');
uicontrol('tag', '0_sendD',   'style', 'pushbutton', 'string', 'v');
uicontrol('tag', '0_user',    'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_factory', 'style', 'pushbutton', 'string', '');

% all controls have the same callback function
ft_uilayout(h, 'tag', '^.*$', 'callback', @cb_interface);

ft_uilayout(h, 'style', 'popupmenu', 'value', 64);  % set the default value to the middle
ft_uilayout(h, 'style', 'slider',    'value', 0.5); % set the default value to the middle

ft_uilayout(h, 'tag', 'control$', 'position', [0 0 060 030]);
ft_uilayout(h, 'tag', 'focus$',   'position', [0 0 060 030]);
ft_uilayout(h, 'tag', 'slide$',   'position', [0 0 070 160]);
ft_uilayout(h, 'tag', 'pan$',     'position', [0 0 070 030]);
ft_uilayout(h, 'tag', 'sendA$',   'position', [0 0 070 030]);
ft_uilayout(h, 'tag', 'sendB$',   'position', [0 0 070 030]);

ft_uilayout(h, 'tag', '^1_', 'hpos', 020);
ft_uilayout(h, 'tag', '^2_', 'hpos', 080);
ft_uilayout(h, 'tag', '^3_', 'hpos', 140);
ft_uilayout(h, 'tag', '^4_', 'hpos', 200);
ft_uilayout(h, 'tag', '^5_', 'hpos', 260);
ft_uilayout(h, 'tag', '^6_', 'hpos', 320);
ft_uilayout(h, 'tag', '^7_', 'hpos', 380);
ft_uilayout(h, 'tag', '^8_', 'hpos', 440);

ft_uilayout(h, 'tag', 'control$', 'vpos', 020);
ft_uilayout(h, 'tag', 'focus$',   'vpos', 050);
ft_uilayout(h, 'tag', 'slide$',   'vpos', 090);
ft_uilayout(h, 'tag', 'pan$',     'vpos', 260);
ft_uilayout(h, 'tag', 'sendA$',   'vpos', 290);
ft_uilayout(h, 'tag', 'sendB$',   'vpos', 320);

ft_uilayout(h, 'tag', 'slide$',   'hshift', -25);

ft_uilayout(h, 'tag', '^0_', 'position', [0 0 20 20]);
ft_uilayout(h, 'tag', '^0_', 'hpos', 530);

ft_uilayout(h, 'tag', '0_record',  'vpos', 105);
ft_uilayout(h, 'tag', '0_solo',    'vpos', 140);
ft_uilayout(h, 'tag', '0_mute',    'vpos', 175);
ft_uilayout(h, 'tag', '0_device',  'vpos', 210);
ft_uilayout(h, 'tag', '0_trackL',  'vpos', 268, 'hshift', -15);
ft_uilayout(h, 'tag', '0_trackR',  'vpos', 268, 'hshift',  15);
ft_uilayout(h, 'tag', '0_sendU',   'vpos', 298, 'hshift', -15);
ft_uilayout(h, 'tag', '0_sendD',   'vpos', 298, 'hshift',  15);
ft_uilayout(h, 'tag', '0_user',    'vpos', 328, 'hshift', -15);
ft_uilayout(h, 'tag', '0_factory', 'vpos', 328, 'hshift',  15);

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


