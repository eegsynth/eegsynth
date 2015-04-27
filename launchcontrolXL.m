function launchcontrolXL(cfg)

% LAUNCHCONTROLXL creates a GUI that emulates the Novation LaunchControl XL
%
% See http://global.novationmusic.com/launch/launch-control-xl
%
% Copyright (C) 2015, Robert Oostenveld

% This file is part of FieldTrip, see http://www.ru.nl/neuroimaging/fieldtrip
% for the documentation and details.
%
%    FieldTrip is free software: you can redistribute it and/or modify
%    it under the terms of the GNU General Public License as published by
%    the Free Software Foundation, either version 3 of the License, or
%    (at your option) any later version.
%
%    FieldTrip is distributed in the hope that it will be useful,
%    but WITHOUT ANY WARRANTY; without even the implied warranty of
%    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%    GNU General Public License for more details.
%
%    You should have received a copy of the GNU General Public License
%    along with FieldTrip. If not, see <http://www.gnu.org/licenses/>.

if isempty(which('ft_defaults'))
  error('this function requires that the FieldTrip toolbox is installed, see http://www.fieldtriptoolbox.org');
else
  % ensure that the FieldTrip path is properly set up
  ft_defaults
end

close all
h = figure;
set(h, 'MenuBar', 'none')
set(h, 'Name', 'LaunchControl XL')
pos = get(h, 'Position');
pos(3) = 580;
pos(4) = 380;
set(h, 'Position', pos);
set(h, 'DeleteFcn', @cb_cleanup);

if nargin<1
  cfg = [];
end

% this table contains the UI tag, channel and note
cfg.mapping = {
  '1_control',       8, 41
  '1_focus',         8, 73
  '1_slide',         8, 77
  '1_pan',           8, 49
  '1_sendB',         8, 29
  '1_sendA',         8, 13
  '2_control',       8, 41+1
  '2_focus',         8, 73+1
  '2_slide',         8, 77+1
  '2_pan',           8, 49+1
  '2_sendB',         8, 29+1
  '2_sendA',         8, 13+1
  '3_control',       8, 41+2
  '3_focus',         8, 73+2
  '3_slide',         8, 77+2
  '3_pan',           8, 49+2
  '3_sendB',         8, 29+2
  '3_sendA',         8, 13+2
  '4_control',       8, 41+3
  '4_focus',         8, 73+3
  '4_slide',         8, 77+3
  '4_pan',           8, 49+3
  '4_sendB',         8, 29+3
  '4_sendA',         8, 13+3
  '5_control',       8, 41+4
  '5_focus',         8, 73+4
  '5_slide',         8, 77+4
  '5_pan',           8, 49+4
  '5_sendB',         8, 29+4
  '5_sendA',         8, 13+4
  '6_control',       8, 41+5
  '6_focus',         8, 73+5
  '6_slide',         8, 77+5
  '6_pan',           8, 49+5
  '6_sendB',         8, 29+5
  '6_sendA',         8, 13+5
  '7_control',       8, 41+6
  '7_focus',         8, 73+6
  '7_slide',         8, 77+6
  '7_pan',           8, 49+6
  '7_sendB',         8, 29+6
  '7_sendA',         8, 13+6
  '8_control',       8, 41+7
  '8_focus',         8, 73+7
  '8_slide',         8, 77+7
  '8_pan',           8, 49+7
  '8_sendB',         8, 29+7
  '8_sendA',         8, 13+7
  '0_record',        8, 0
  '0_solo',          8, 0
  '0_mute',          8, 0
  '0_device',        8, 0
  '0_trackL', 8, 0
  '0_trackR', 8, 0
  '0_sendU',  8, 0
  '0_sendD',  8, 0
  };

guidata(h, cfg);

uicontrol('tag', '1_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '1_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '1_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '1_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '2_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '2_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '2_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '2_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '3_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '3_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '3_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '3_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '4_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '4_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '4_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '4_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '5_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '5_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '5_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '5_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '6_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '6_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '6_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '6_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '7_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '7_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '7_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '7_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '8_control', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '8_focus',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '8_slide',   'callback', @cb_interface, 'style', 'slider',     'string', '');
uicontrol('tag', '8_pan',     'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '8_sendB',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));
uicontrol('tag', '8_sendA',   'callback', @cb_interface, 'style', 'popupmenu',  'string', num2cell(1:127));

uicontrol('tag', '0_record',  'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_solo',    'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_mute',    'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_device',  'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_trackL',  'callback', @cb_interface, 'style', 'pushbutton', 'string', '<');
uicontrol('tag', '0_trackR',  'callback', @cb_interface, 'style', 'pushbutton', 'string', '>');
uicontrol('tag', '0_sendU',   'callback', @cb_interface, 'style', 'pushbutton', 'string', '^');
uicontrol('tag', '0_sendD',   'callback', @cb_interface, 'style', 'pushbutton', 'string', 'v');
uicontrol('tag', '0_user',    'callback', @cb_interface, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_factory', 'callback', @cb_interface, 'style', 'pushbutton', 'string', '');

ft_uilayout(h, 'style', 'popupmenu', 'value', 64); % set the default to '0'

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

t = timer('ExecutionMode', 'fixedRate', 'Period', 0.1, 'UserData', h, 'TimerFcn', @cb_timer);
start(t);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_timer(t, varargin)
persistent tag channel note

dat = midiIn('G');
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
    if ~isempty(regexp(tag{sel}, 'slide$'))
      ft_uilayout(h, 'tag', tag{sel}, 'Value', dat(i,3)/127);
    else
      ft_uilayout(h, 'tag', tag{sel}, 'Value', dat(i,3));
    end
  end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_cleanup(varargin)
delete(timerfindall)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_interface(h, varargin)
disp(get(h, 'tag'))
