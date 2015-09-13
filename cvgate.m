classdef cvgate
  
  % CVGATE creates an object to control the Arduino based CV/Gate interface
  % that is described at http://www.ouunpo.com/eegsynth/?p=268
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
  %     a.voltage = 5 * (0.5 + sin(2*pi*toc(t))/2);  % fluctuate at 1 Hz
  %     a.gate    = ~a.gate;                         % flip the gate on and off
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
    delay     = 0.005;
  end
  
  properties (SetAccess = public)
    voltage = 0;
    gate    = 0;
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
      fopen(obj.device);
    end % constructor
    
    function delete(obj)
      flushinput(obj.device);
      flushoutput(obj.device);
      fclose(obj.device);
      delete(obj.device);
    end % destructor
    
    function update(obj)
      if ~isempty(obj.voltage)
        cmd = sprintf('*c1v%04d#', round((2^12-1)*obj.voltage/5));
        fprintf(obj.device, cmd);
      end
      if ~isempty(obj.gate)
        cmd = sprintf('*g1v%d#', double(obj.gate));
        fprintf(obj.device, cmd);
      end
      flushinput(obj.device);
      flushoutput(obj.device);
      pause(obj.delay);
    end % update
    
    function obj = set.voltage(obj, voltage)
      assert(isscalar(voltage));
      obj.voltage = min(max(0, voltage), 5);
    end % set
    
    function obj = set.gate(obj, gate)
      assert(isscalar(gate));
      obj.gate = (gate~=0);
    end % set
    
  end % methods
end % classdef
