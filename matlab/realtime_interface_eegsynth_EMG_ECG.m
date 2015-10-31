function realtime_interface_eegsynth_EMG_ECG(cfg)

% REALTIME_INTERFACE_EEGSYNTH is an example realtime application for online
% viewing of realtime data, and the return of MIDI codes in a
% neurofeedback. It should work both for EEG and MEG. This file is part of
% EEGSYNTH. See eegsynth.com,
% https://github.com/stephenwhitmarsh/eegsynth-matlab and
% https://github.com/oostenveld/eegsynth-matlab for documentation and
% details.
%
%    EEGSYNTH is free software: you can redistribute it and/or modify it
%    under the terms of the GNU General Public License as published by
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
%
% Use as
%   realtime_interface_eegsynth(cfg,cfg)
%
% The source of the data is configured in the first cfg:
%   cfg.dataset       = string
% or alternatively to obtain more low-level control as
%   cfg.datafile      = string
%   cfg.headerfile    = string
%   cfg.eventfile     = string
%   cfg.dataformat    = string, default is determined automatic
%   cfg.headerformat  = string, default is determined automatic
%   cfg.eventformat   = string, default is determined automatic
%
% the second configuration option is a struct, of a variable size, with each being a complete set of configurations for a 'patch',
% with the following options:
%
%   cfg.blocksize       = number, size of the blocks/chuncks that are read (default = 1 second)
%   cfg.analysiswindow  = seconds, timewindow of analysis. Typically longer
%                             than blocksize, to allow a more smooth, stable analysis window, with higher freq.
%                             resolution.
%   cfg.histsize        = number, number of blocks - determed in cfg.blocksize - that is used for
%                             normalization of amplitude or power.
%   cfg.channel         = cell-array of virtual channel, see FT_CHANNELSELECTION (default = 'all').
%                             channels will be averaged before processing by the path
%   cfg.demean          = 'no' or 'yes', whether to apply baseline correction (default = 'yes')
%   cfg.bufferdata      = whether to start on the 'first or 'last' data that is available (default = 'last')
%   cfg.jumptoeof       = whether to skip to the end of the stream/file at startup (default = 'yes')
%   cfg.readevent       = whether or not to copy events (default = 'no')
%   cfg.feedbackchan    = number, MIDI channel for output

%   cfg.type is a string, that determines by which patch a virtual channel is processed
%   and displayed, currently we have:

%   cfg.type            = 'amp2gate'
%                             Normalizes data according to max of absolute of past (see: cfg.histsize), applying
%                             a threshold on last read data (see: cfg.blocksize). If threshold is reached, a note
%                             is send to a MIDI channel (see: cfg.feedbackchan).

%   cfg.type             = 'pow2CV': Displays power according to cfg.foilim, scales it according to cfg.powscale,
%                              and sends out a MIDI code depending on the scaled value of the frequency of interest, determined
%                              by cfg.feedbackfoi


% Some notes about skipping data and catching up with the data stream:
%
% cfg.jumptoeof='yes' causes the realtime function to jump to the end when the
% function _starts_. It causes all data acquired prior to starting the realtime
% function to be skipped.
%
% cfg.bufferdata='last' causes the realtime function to jump to the last available data
% while _running_. If the realtime loop is not fast enough, it causes some data to be
% dropped.
%
% If you want to skip all data that was acquired before you start the RT function,
% but don't want to miss any data that was acquired while the realtime function is
% started, then you should use jumptoeof=yes and bufferdata=first. If you want to
% analyse data from a file, then you should use jumptoeof=no and bufferdata=first.
%
% To stop this realtime function, you have to press Ctrl-C

% Copyright (C) 2008, Robert Oostenveld
%
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
%
% $Id: ft_realtime_signalviewer.m 10300 2015-03-29 17:34:39Z roboos $

% set the default configuration options
if ~isfield(cfg, 'dataformat'),     cfg.dataformat = [];                end % default is detected automatically
if ~isfield(cfg, 'headerformat'),   cfg.headerformat = [];              end % default is detected automatically
if ~isfield(cfg, 'eventformat'),    cfg.eventformat = [];               end % default is detected automatically
if ~isfield(cfg, 'jumptoeof'),      cfg.jumptoeof = 'yes';              end % jump to end of file at initialization
if ~isfield(cfg, 'bufferdata'),     cfg.bufferdata = 'all';             end % first, last, or all. The latter I added and works very nicely
if ~isfield(cfg, 'blocksize'),      cfg.blocksize = 0.250;              end
if ~isfield(cfg, 'windowsize_EMG'), cfg.windowsize_EMG = cfg.blocksize *5;   end
if ~isfield(cfg, 'windowsize_ECG'), cfg.windowsize_ECG = cfg.blocksize *20;  end
if ~isfield(cfg, 'overlap'),        cfg.overlap = 0;                    end % in seconds
if ~isfield(cfg, 'channel'),        cfg.channel = 'all';                end
if ~isfield(cfg, 'readevent'),      cfg.readevent = 'no';               end % capture events?
if ~isfield(cfg, 'demean'),         cfg.demean = 'yes';                 end % baseline correction
if ~isfield(cfg, 'notch'),          cfg.notch = 'no';                   end % baseline correction
if ~isfield(cfg, 'histsize'),       cfg.histsize = 20;                  end % baseline correction
if ~isfield(cfg, 'type'),           cfg.type = 'off';                   end % in percentage above or below 50%
if ~isfield(cfg, 'foilim'),         cfg.foilim = [5 40];                end %
if ~isfield(cfg, 'feedbackfoi'),    cfg.feedbackfoi = [];               end %
if ~isfield(cfg, 'feedbackamp'),    cfg.feedbackamp = [];               end % in percentage above or below 50%
if ~isfield(cfg, 'polyremoval'),    cfg.polyremoval = 'no';             end
if ~isfield(cfg, 'hpfilter'),       cfg.hpfilter = 'yes';                end
if ~isfield(cfg, 'hpfreq'),         cfg.hpfreq = 30;                    end

if ~isfield(cfg, 'lpfilter'),       cfg.lpfilter = 'no';                end
if ~isfield(cfg, 'refchannel'),     cfg.refchannel = [];                end % not added in this patch, but will do - separete ref(s) per channel.
if ~isfield(cfg, 'dataset')         && ~isfield(cfg, 'header') && ~isfield(cfg, 'datafile') cfg.dataset = 'buffer://10.9.25.37:1972'; end;

global scaling calibrating keeprunning portamento threshold timechan
if ~isfield(cfg, 'scaling'),        scaling     = ones(8,1);            end
if ~isfield(cfg, 'calibration'),    calibration = ones(8,1);            end
if ~isfield(cfg, 'portamento'),     portamento  = zeros(8,1);           end
if ~isfield(cfg, 'thresold'),       threshold   = zeros(8,1);           end
if ~isfield(cfg, 'timechan'),       timechan    = 1;                    end

warning off

calibrating = 0;
keeprunning = true;

ft_defaults

% figure
h = figure;
set(h, 'DeleteFcn', @cb_cleanup);
set(h, 'MenuBar', 'none')
set(h, 'Name', 'BrainSynth Controller')
    
% initialize MIDI
midiOpen('output');
midiOpen('input');

% translate dataset into datafile+headerfile
cfg = ft_checkconfig(cfg, 'dataset2files', 'yes');
cfg = ft_checkconfig(cfg, 'required', {'datafile' 'headerfile'});

% ensure that the persistent variables related to caching are cleared
clear ft_read_header
hdr = ft_read_header(cfg.headerfile, 'headerformat', cfg.headerformat, 'cache', true, 'retry', true);

for i = 1 : size(cfg,2);
    if strcmp(cfg.jumptoeof, 'yes')
        prevSample(i) = hdr.nSamples * hdr.nTrials;
    else
        prevSample(i) = 0;
    end
end

% determine the size of blocks to process
blocksize = round(cfg.blocksize * hdr.Fs);
overlap   = round(cfg.overlap * hdr.Fs);
analysiswindow = zeros(8,cfg.windowsize_EMG*hdr.Fs);
analysiswindow_ECG = zeros(8,cfg.windowsize_ECG*hdr.Fs);

t = timer('ExecutionMode', 'fixedRate', 'Period', 0.1, 'TimerFcn', @cb_timer);
start(t);

count       = 0;
history_cal = [];
history     = ones(8,cfg.histsize);

while keeprunning
    
    % determine number of samples available in buffer
    hdr = ft_read_header(cfg.headerfile, 'headerformat', cfg.headerformat, 'cache', false);
    
    % see whether new samples are available
    newsamples = hdr.nSamples*hdr.nTrials-prevSample;
    
    % if so, run the follow
    if newsamples >= blocksize || (strcmp(cfg.bufferdata, 'all') && newsamples > 1)        
        if strcmp(cfg.bufferdata, 'last')
            begsample  = hdr.nSamples*hdr.nTrials - blocksize + 1;
            endsample  = hdr.nSamples*hdr.nTrials;
        elseif strcmp(cfg.bufferdata, 'first')
            begsample  = prevSample+1;
            endsample  = prevSample+blocksize ;
        elseif strcmp(cfg.bufferdata, 'all')
            begsample  = prevSample+1;
            endsample  = hdr.nSamples*hdr.nTrials ;
            if endsample-begsample > blocksize
                disp(sprintf('CAUTION: %d more samples available than blocksize, restricting readout to blocksize - losing data', endsample-begsample-blocksize ));
                begsample  = hdr.nSamples*hdr.nTrials - blocksize + 1;
                endsample  = hdr.nSamples*hdr.nTrials;
            end
        else
            error('unsupported value for cfg.bufferdata');
        end
        
        % this allows overlapping data segments
        if overlap && (begsample>overlap)
            begsample = begsample - overlap;
            endsample = endsample - overlap;
        end
        
        % remember up to where the data was read
        prevSample  = endsample;
        count       = count + 1;
        
        % read data segment from buffer
        dat = ft_read_data(cfg.datafile, 'header', hdr, 'dataformat', cfg.dataformat, 'chanindx', 1:8, 'begsample', begsample, 'endsample', endsample, 'checkboundary', false);
%         dat = [eye(4) -eye(4); eye(4) zeros(4)] * dat;
        % update analysiswindow with new data: last in = first out
        analysiswindow(:,1:end-size(dat,2))     = analysiswindow(:,size(dat,2)+1:end);
        analysiswindow(:,end-size(dat,2)+1:end) = dat;
        
        analysiswindow_ECG(:,1:end-size(dat,2))     = analysiswindow_ECG(:,size(dat,2)+1:end);
        analysiswindow_ECG(:,end-size(dat,2)+1:end) = dat;
        
        % apply detrending & filtering on ECG
        dat_preproc_ECG =  ft_preproc_polyremoval(analysiswindow_ECG, 1);
        dat_preproc_ECG =  ft_preproc_lowpassfilter(dat_preproc_ECG, hdr.Fs, 30, 3, 'but', 'twopass');
        
        
        % scale ECG
        m = max(abs(dat_preproc_ECG),[],2);
        for i = 1 : 8
            dat_preproc_ECG(i,:) = dat_preproc_ECG(i,:) ./ m(i);
        end
        
        % apply some preprocessing options but save unpreprocessed
        % analysiswindow because it often does not make sense to append
        % data after it has been separately preprocessed
        dat_preproc = analysiswindow;
        
        if strcmp(cfg.demean, 'yes')
            dat_preproc = ft_preproc_baselinecorrect(dat_preproc);
        end
        if strcmp(cfg.notch, 'yes')
            dat_preproc = ft_preproc_bandstopfilter(dat_preproc, hdr.Fs, [45 55], 3, 'but', 'twopass');
        end
        if strcmp(cfg.polyremoval, 'yes')
            dat_preproc =  ft_preproc_polyremoval(dat_preproc, 1);
        end
        if strcmp(cfg.hpfilter, 'yes')
            dat_preproc =  ft_preproc_highpassfilter(dat_preproc, hdr.Fs, cfg.hpfreq, 3, 'but', 'twopass');
        end
        if strcmp(cfg.lpfilter, 'yes')
            dat_preproc =  ft_preproc_lowpassfilter(dat_preproc, hdr.Fs, cfg.lpfreq, 3, 'but', 'twopass');
        end
                
        % need to keep dat_rms for calibration 
        dat_rms = sqrt(mean(dat_preproc.^2,2));
        
        % scale data according to calibration and manual scaling with
        % Launch Control
        dat_scaled = dat_rms.*calibration.*scaling;
        
        % update history
        history(:,1:end-1) = history(:,2:end);
        history(:,end) = dat_scaled;
        
        % calibration
        if calibrating > 0
            history_cal = [history_cal dat_rms];
            if calibrating == 9
                disp('Calibrating all channels');
            else
                disp(['Calibrating channel: ', num2str(calibrating)]);
            end
            if size(history_cal,2) > 40
                if calibrating == 9
                    calibration = 1.2 ./ max(history_cal,[],2);        
                else
                    calibration(calibrating) = 1.2 ./ max(history_cal(calibrating,:));
                end
                calibrating = 0;
                history_cal = [];
                disp('Done calibrating!');
            end
        end
        
        % figure - now just redrawing everything. Works fast enough.
        subplot(5,1,2);

        bar(ones(1,8),'g');
        hold on
        bar(threshold,'r');
        bar(dat_scaled, 0.4);
        axis([xlim 0 1]);

        hold off
        
        subplot(5,1,3);
        imagesc(history,[0 2]);
        axis off
        axis tight
        
        subplot(5,1,4);
        bar(scaling);
        ax = axis;
        axis([ax(1) ax(2) 0 2]);
               
        subplot(5,1,5);
        bar(portamento);
        ax = axis;
        axis([ax(1) ax(2) 0 1]);
        
        subplot(5,1,1);
        plot(dat_preproc_ECG(timechan,:)); 
        axis tight
        axis([xlim -1 1]);
        hold on
        thresh = (threshold(timechan)-0.5)*2;
        plot(xlim, [thresh thresh],'r');
        plot([size(dat_preproc_ECG,2)-blocksize,  size(dat_preproc_ECG,2)-blocksize],ylim,'g');
        
        hold off
        
        
        
        drawnow;
        
        % output MIDI EMG CV&gate
        if (threshold(timechan)-0.5)*2 >= 0
            midiGate(timechan,max(dat_preproc_ECG(timechan, end-blocksize:end)),(threshold(timechan)-0.5)*2);
        else
            midiGate(timechan,min(dat_preproc_ECG(timechan, end-blocksize:end)),(threshold(timechan)-0.5)*2);
        end
        for i = 1 : 8
            midiPortamento(i,portamento(i));      % MIDI setting for portamento/glide that also the Shuttle Control uses nicely. Only have to set it once (per channel)
            midiNote_half(i,dat_scaled(i));       % _half until I fixed the fact that 1) I can't seem to be able to use both 7bit values, and 2) JL's synth uses only 0-5, instead of -5 to 5 Volts
            if i ~= timechan
                midiGate(i,dat_scaled(i),threshold(i));
            end
        end      
    end
end % if enough new samples

cb_cleanup;
close(h);
clear all % FIXME should only clear midi

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTIONS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [time] = offset2time(offset, fsample, nsamples)
offset   = double(offset);
nsamples = double(nsamples);
time = (offset + (0:(nsamples-1)))/fsample;

function cb_timer(t, varargin)
% persistent tag channel note
global scaling calibrating keeprunning portamento threshold timechan
datMIDI = midiIn('G');

if isempty(datMIDI)
  return
end

for i=1:size(datMIDI,1)
    fprintf('input: channel %3d, note %3d, velocity %3d, timestamp %d\n', datMIDI(i,1), datMIDI(i,2), datMIDI(i,3), datMIDI(i,4));
    
    if any(datMIDI(i,2) == [13:13+7])
        scaling(datMIDI(i,2) - 12) = datMIDI(i,3)/64;
        fprintf('scaling channel %3d by %d\n', datMIDI(i,2) - 12,datMIDI(i,3)/64);        
    end
    if any(datMIDI(i,2) == [29:29+7])
        portamento(datMIDI(i,2) - 28) = datMIDI(i,3)/127;
        fprintf('portamento channel %3d: %d\n', datMIDI(i,2) - 28,datMIDI(i,3)/127);        
    end
    if any(datMIDI(i,2) == [77:77+7])
        threshold(datMIDI(i,2) - 76) = datMIDI(i,3)/127;
        fprintf('threshold channel %3d: %d\n', datMIDI(i,2) - 76,datMIDI(i,3)/127);        
    end
    if any(datMIDI(i,2) == [41:44])
        timechan = datMIDI(i,2) - 40;
        fprintf('timecourse channel %3d\n', datMIDI(i,2));        
    end
    if any(datMIDI(i,2) == [56:60])
        timechan = datMIDI(i,2) - 52;
        fprintf('timecourse channel %3d\n', datMIDI(i,2));
    end
    if any(datMIDI(i,2) == [73:76])
        calibrating = datMIDI(i,2) - 72;
    end
    if datMIDI(i,2) == 105
        keeprunning = false;
    end
    if datMIDI(i,2) == 108
        calibrating = 9;
    end    
    if datMIDI(i,2) == 105
        keeprunning = false;
    end
end

function cb_cleanup(varargin)
delete(timerfindall);

function midiPitchBend(channel,value)
if value < 0 
    value = 0;
end
if value > 1
    value = 1;
end
value = round(value*4096);
midiOut(uint8([223+channel floor(value/127) mod(value,127)]));

function midiGate(channel,value,thresh)
if thresh >= 0
    if value > thresh
        midiout('+', channel+8,127, 127);
    else
        midiout('.', channel+8,127, 0);
    end
else
    if value < thresh
        midiout('+', channel+8,127, 127);
    else
        midiout('.', channel+8,127, 0);
    end
end

function midiNote(channel,value)
if value < 0 
    value = 0;
end
if value > 1
    value = 1;
end
value = round(value * 120 + 6);
midiOut('+', channel, value, 126);
if channel == 1
    disp(value);
end

function midiPitchBend_half(channel,value) % _half until I fixed the fact that 1) I can't seem to be able to use both 7bit values, and 2) JL's synth uses only 0-5, instead of -5 to 5 Volts
if value < 0 
    value = 0;
end
if value > 1
    value = 1;
end
value = round(value*63)+65;
midiOut(uint8([223+channel floor(value/127) mod(value,127)]))

function midiNote_half(channel,value) % _half as above
if value < 0 
    value = 0;
end
if value > 1
    value = 1;
end
value = round(value*63)+65;
midiOut('+', channel, value, 126);

function midiPortamento(channel,value) 
if value < 0 
    value = 0;
end
if value > 1
    value = 1;
end
value = round(value * 126);
% CC#5
midiOut(uint8([175+channel 5 value]));

