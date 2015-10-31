function a = cvgateOpen(a)

% CVGATEOPEN opens a graphical user interface to select the serial port
% to which the Arduino USB2CVGATE interface is connected. Subsequently, it
% allows testing the analog (cv) and digital (gate) outputs.
%
% Use as
%   obj = cvgateOpen
% or as
%   cvgateOpen(obj)
% if the serial port has already been opened.
%
% See also MIDIOPEN, CVGATE

% This file is part of EEGSYNTH, see https://github.com/oostenveld/eegsynth-matlab
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

% clean up old devices
d = instrfindall;
while ~isempty(d)
  delete(d(end));
  d = instrfindall;
end

if nargin<1
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % part 1: determine the serial port
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  
  h = dialog;
  set(h, 'MenuBar', 'none')
  set(h, 'Name', 'Select serial port')
  
  if ispc
    L = struct();
    prefix = '';
    for i=1:8
      L(i).name = sprintf('COM%d', i);
    end
  else
    prefix = '/dev/';
    L = dir(fullfile(prefix, 'tty.*usb*'));
  end
  
  hpos = 10;
  vpos = 10;
  for i=1:length(L)
    uicontrol(h, 'style', 'pushbutton', 'position', [hpos vpos 240 20], 'tag', num2str(i), 'string', L(i).name, 'callback', @cb_interface);
    vpos = vpos + 30;
  end
  
  uicontrol(h, 'style', 'pushbutton', 'position', [hpos vpos 240 20], 'tag', num2str(i), 'string', 'None', 'callback', @cb_none);
  vpos = vpos + 30;
  
  % update the size according to the number of buttons
  pos = get(h, 'position');
  pos(1) = pos(1)+pos(3)/2-360/2;
  pos(3) = 260;
  pos(4) = vpos;
  set(h, 'position', pos);
  
  uiwait(h);
  if ishandle(h)
    n = str2num(guidata(h)); %#ok<*ST2NM>
    delete(h);
    a = cvgate(fullfile(prefix, L(n).name), 115200);
    a.voltage = [0 0 0 0];
    a.gate    = [0 0 0 0];
  else
    a = [];
  end
end % determine serial port

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% part 2: control the voltage and gate
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

if ~isempty(a)
  h = figure;
  
  set(h, 'MenuBar', 'none')
  set(h, 'ToolBar', 'none')
  set(h, 'Name', 'Set voltage and gate')
  pos = get(h, 'position');
  pos(3) = 430;
  pos(4) = 100;
  
  set(h, 'position', pos);
  guidata(h, a);
  
  c1 = uicontrol('style', 'slider', 'tag', 'c1', 'min', 0, 'max', 4095, 'sliderstep', [32 512]/4095, 'callback', @update_slider);
  g1 = uicontrol('style', 'slider', 'tag', 'c2', 'min', 0, 'max', 4095, 'sliderstep', [32 512]/4095, 'callback', @update_slider);
  c2 = uicontrol('style', 'slider', 'tag', 'c3', 'min', 0, 'max', 4095, 'sliderstep', [32 512]/4095, 'callback', @update_slider);
  g2 = uicontrol('style', 'slider', 'tag', 'c4', 'min', 0, 'max', 4095, 'sliderstep', [32 512]/4095, 'callback', @update_slider);
  c3 = uicontrol('style', 'slider', 'tag', 'g1', 'min', 0, 'max',    1, 'sliderstep', [1 1], 'callback', @update_slider);
  g3 = uicontrol('style', 'slider', 'tag', 'g2', 'min', 0, 'max',    1, 'sliderstep', [1 1], 'callback', @update_slider);
  c4 = uicontrol('style', 'slider', 'tag', 'g3', 'min', 0, 'max',    1, 'sliderstep', [1 1], 'callback', @update_slider);
  g4 = uicontrol('style', 'slider', 'tag', 'g4', 'min', 0, 'max',    1, 'sliderstep', [1 1], 'callback', @update_slider);
  
  ft_uilayout(h, 'tag', 'c1', 'width', 200, 'hpos', 10, 'vpos', 70);
  ft_uilayout(h, 'tag', 'c2', 'width', 200, 'hpos', 10, 'vpos', 50);
  ft_uilayout(h, 'tag', 'c3', 'width', 200, 'hpos', 10, 'vpos', 30);
  ft_uilayout(h, 'tag', 'c4', 'width', 200, 'hpos', 10, 'vpos', 10);
  ft_uilayout(h, 'tag', 'g1', 'width', 200, 'hpos', 220, 'vpos', 70);
  ft_uilayout(h, 'tag', 'g2', 'width', 200, 'hpos', 220, 'vpos', 50);
  ft_uilayout(h, 'tag', 'g3', 'width', 200, 'hpos', 220, 'vpos', 30);
  ft_uilayout(h, 'tag', 'g4', 'width', 200, 'hpos', 220, 'vpos', 10);
end

if ~nargout
  % no output is needed
  clear a
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function update_slider(h, varargin)
a = guidata(h);
switch get(h, 'tag')
  case 'c1'
    a.voltage(1) = get(h, 'value');
    set(h, 'value', a.voltage(1));
  case 'c2'
    a.voltage(2) = get(h, 'value');
    set(h, 'value', a.voltage(2));
  case 'c3'
    a.voltage(3) = get(h, 'value');
    set(h, 'value', a.voltage(3));
  case 'c4'
    a.voltage(4) = get(h, 'value');
    set(h, 'value', a.voltage(4));
  case 'g1'
    a.gate(1) = get(h, 'value');
    set(h, 'value', a.gate(1));
  case 'g2'
    a.gate(2) = get(h, 'value');
    set(h, 'value', a.gate(2));
  case 'g3'
    a.gate(3) = get(h, 'value');
    set(h, 'value', a.gate(3));
  case 'g4'
    a.gate(4) = get(h, 'value');
    set(h, 'value', a.gate(4));
end
disp(a);
update(a);
guidata(get(h, 'parent'), a);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_interface(h, varargin)
guidata(get(h, 'parent'), get(h, 'tag'));
uiresume(get(h, 'parent'));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function cb_none(h, varargin)
delete(get(h, 'parent'));
