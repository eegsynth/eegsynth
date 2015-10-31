function eegcontroller(cfg)

% EEGCONTROLLER
%
% Use as
%   eegcontroller(cfg)
% with the following configuration options
%   cfg.channel    = cell-array, see FT_CHANNELSELECTION (default = 'all')
%   cfg.foilim     = [Flow Fhigh] (default = [1 45])
%   cfg.blocksize  = number, size of the blocks/chuncks that are processed (default = 1 second)
%   cfg.bufferdata = whether to start on the 'first or 'last' data that is available (default = 'last')
%
% The source of the data is configured as
%   cfg.dataset       = string
% or alternatively to obtain more low-level control as
%   cfg.datafile      = string
%   cfg.headerfile    = string
%   cfg.eventfile     = string
%   cfg.dataformat    = string, default is determined automatic
%   cfg.headerformat  = string, default is determined automatic
%   cfg.eventformat   = string, default is determined automatic


% set the default configuration options
cfg.dataformat    = ft_getopt(cfg, 'dataformat', []);   % default is detected automatically
cfg.headerformat  = ft_getopt(cfg, 'headerformat', []); % default is detected automatically
cfg.eventformat   = ft_getopt(cfg, 'eventformat', []);  % default is detected automatically
cfg.blocksize     = ft_getopt(cfg, 'blocksize', 0.05);  % stepsize, in seconds
cfg.channel       = ft_getopt(cfg, 'channel', 'all');
cfg.bufferdata    = ft_getopt(cfg, 'bufferdata', 'last'); % first or last
cfg.dataset       = ft_getopt(cfg, 'dataset', 'buffer:\\localhost:1972');
cfg.foilim        = ft_getopt(cfg, 'foilim', [1 30]);
cfg.windowsize    = ft_getopt(cfg, 'windowsize', 2);  % length of sliding window, in seconds
cfg.scale         = ft_getopt(cfg, 'scale', 1);       % can be used to fix the calibration
cfg.feedback      = ft_getopt(cfg, 'feedback', 'no'); % use neurofeedback with MIDI, yes or no
cfg.bpfreq        = ft_getopt(cfg, 'bpfreq', [2 45]);

% translate dataset into datafile+headerfile
cfg = ft_checkconfig(cfg, 'dataset2files', 'yes');
cfg = ft_checkconfig(cfg, 'required', {'datafile' 'headerfile'});

% ensure that the persistent variables related to caching are cleared
clear ft_read_header

% start by reading the header from the realtime buffer
hdr = ft_read_header(cfg.headerfile, 'cache', true, 'retry', true);

% define a subset of channels for reading and processing
cfg.channel = ft_channelselection(cfg.channel, hdr.label);
chanindx = match_str(hdr.label, cfg.channel);
nchan = length(chanindx);
label = hdr.label(chanindx);

% determine the size of blocks to process
blocksize = round(cfg.blocksize * hdr.Fs)
prevSample = 0;
count = 0;
h = [];

while (true)
  
  hdr = ft_read_header(cfg.headerfile, 'cache', true);
  
  % see whether new samples are available
  newsamples = (hdr.nSamples*hdr.nTrials-prevSample);
  
  if newsamples>=blocksize && (hdr.nSamples*hdr.nTrials/hdr.Fs)>cfg.windowsize
    
    % determine the samples to process
    if strcmp(cfg.bufferdata, 'last')
      begsample = hdr.nSamples*hdr.nTrials - round(cfg.windowsize*hdr.Fs) + 1;
      endsample = hdr.nSamples*hdr.nTrials;
    elseif strcmp(cfg.bufferdata, 'first')
      begsample = prevSample+1;
      endsample = prevSample+blocksize ;
    else
      error('unsupported value for cfg.bufferdata');
    end
    
    % remember up to where the data was read
    prevSample = endsample;
    count = count + 1;
    fprintf('processing segment %d from sample %d to %d\n', count, begsample, endsample);
    
    % read the data segment from buffer
    dat = ft_read_data(cfg.datafile, 'header', hdr, 'begsample', begsample, 'endsample', endsample, 'chanindx', chanindx, 'checkboundary', false);
    
    % construct a matching time axis
    time = ((begsample:endsample)-1)/hdr.Fs;
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % from here onward it is specific to the application
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    dat = ft_preproc_bandpassfilter(dat, hdr.Fs, cfg.bpfreq);
    dat = cfg.scale * dat;
    
    if ishandle(h)
      figure(h);
    else
      h = figure;
    end
    
    for i=1:nchan
      subplot(nchan, 2, 2*i-1);
      plot(dat(i,:));
      axis off
      subplot(nchan, 2, 2*i);
      plot(dat(i,:));
      axis off
    end
    
  end % enough samples
  
end % while true
