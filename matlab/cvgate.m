classdef cvgate
  
  % CVGATE creates an object to control the Arduino based CV/Gate interface
  % that is described at http://www.ouunpo.com/eegsynth/?p=268. Control
  % voltage values are specified between 0 and 4095. For the 1-channel
  % version this maps to 0-5 Volt, for the 4-channel version this maps to
  % 0-10 Volt.
  %
  % Example use:
  %
  %   a = cvgate('/dev/tty.usbserial-AH01DRO4', 115200);
  %
  %   a.voltage = 0;
  %   a.gate    = 0;
  %
  %   c = 0;
  %   t = tic;
  %   while true
  %     a.voltage = 4095 * (0.5 + 0.5*sin(2*pi*toc(t)));  % fluctuate at 1 Hz
  %     a.gate    = ~a.gate;                              % toggle the gate on and off
  %     update(a);
  %     c = c + 1;
  %     if mod(c, 100)==0
  %       % display the number of updates per second
  %       disp(c/toc(t));
  %     end
  %   end
  
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
  
  properties (Hidden)
    device
    port      = '/dev/tty.usbserial-AH01DRO4'
    baudrate  = 115200;
  end
  
  properties (SetAccess = public)
    voltage   = [];
    gate      = [];
    delay     = 0;
  end
  
  % Class methods
  methods
    function obj = cvgate(port, baudrate)
      if nargin>0 && ~isempty(port)
        obj.port = port;
      end
      if nargin>1 && ~isempty(baudrate)
        obj.baudrate = baudrate;
      end
      obj.device = serial(obj.port, 'BaudRate', obj.baudrate);
      try
        fopen(obj.device);
        pause(1);
        flushinput(obj.device);
      catch
        p = instrfind('Type', 'serial', 'Port', obj.port);
        if isobject(p)
          delete(p);
        end
      end
    end % constructor
    
    function delete(obj)
      flushoutput(obj.device);
      flushinput(obj.device);
      fclose(obj.device);
      delete(obj.device);
    end % destructor
    
    function update(obj)
      if ~isempty(obj.voltage)
        cmd = sprintf('*c%dv%04d#', [1:numel(obj.voltage); round((2^12-1)*obj.voltage/4095)]);
        fprintf(obj.device, cmd);
      end
      if ~isempty(obj.gate)
        cmd = sprintf('*g%dv%d#', [1:numel(obj.gate); double(obj.gate)]);
        fprintf(obj.device, cmd);
      end
      flushoutput(obj.device);
      flushinput(obj.device);
      pause(obj.delay);
    end % update
    
    function obj = set.voltage(obj, voltage)
      assert(isempty(voltage) || isvector(voltage));
      obj.voltage = min(max(0, round(voltage(:))'), 4095);
    end % set
    
    function obj = set.gate(obj, gate)
      assert(isempty(gate) || isvector(gate));
      obj.gate = (gate(:)'~=0);
    end % set
    
  end % methods
end % classdef
