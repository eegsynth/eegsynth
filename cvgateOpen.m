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
% See also MIDIOPEN

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
  pos(3) = 220;
  pos(4) = 60;
  
  set(h, 'position', pos);
  guidata(h, a);
  
  ch = uicontrol('style', 'slider', 'tag', 'row1', 'min', 0, 'max', 5, 'sliderstep', [0.01 0.05], 'callback', @update_voltage);
  gh = uicontrol('style', 'slider', 'tag', 'row2', 'min', 0, 'max', 1, 'sliderstep', [1.00 1.00], 'callback', @update_gate);
  
  ft_uilayout(h, 'tag', 'row1', 'width', 200, 'hpos', 10, 'vpos', 30);
  ft_uilayout(h, 'tag', 'row2', 'width', 200, 'hpos', 10, 'vpos', 10);
end

if ~nargout
  % no output is needed
  clear a
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function update_voltage(h, varargin)
a = guidata(h);
a.voltage = get(h, 'value');
set(h, 'value', a.voltage);
update(a);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function update_gate(h, varargin)
a = guidata(h);
a.gate = get(h, 'value');
set(h, 'value', a.gate);
update(a);

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
