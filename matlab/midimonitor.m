function midimonitor(cfg)

% MIDIMONITOR monitors an input MIDI channel and displays the messages on screen.
%
% Copyright (C) 2015, Robert Oostenveld

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

if nargin<1
  cfg = [];
end

% get the options, use defaults where needed
cfg.input    = ft_getopt(cfg, 'input', 'yes');    % yes, no

if strcmp(cfg.input, 'yes')
  midiOpen('input');
end

while (true)
  
  in  = midiIn('G');
  
  for i=1:size(in,1)
    fprintf('input: channel %3d, note %3d, velocity %3d, timestamp %d\n', in(i,1), in(i,2), in(i,3), in(i,4));
  end
  
end % while true
