function signals = readBioFile(filePath)
fileID = fopen(filePath, 'r');

% 1. Read metadata
% 1.1. Read number of signal
nSignals = fread(fileID, 1, 'uint32');
% 1.2. Read "base" sampling rate and number of samples (i.e., for timestamp and
% trigger)
fsBase = fread(fileID, 1, 'float32');
nSampBase = fread(fileID, 1, 'uint32');
% 1.3. For each signal, read signal name, sampling rate, number of samples and of channels
signals = struct();
for i = 1:nSignals
    sigNameLen = fread(fileID, 1, 'uint32');
    sigName = fread(fileID, sigNameLen, '*char');
    sigName = string(sigName');
    fs = fread(fileID, 1, 'float32');
    nSamp = fread(fileID, 1, 'uint32');
    nCh = fread(fileID, 1, 'uint32');
    signals.(sigName) = struct('fs', fs, 'nSamp', nSamp, 'nCh', nCh);
end
% 1.4. Read whether the trigger is available
isTrigger = fread(fileID, 1, 'uint8');
isTrigger = logical(bitand(isTrigger, 1));

% 2. Read actual signals
% 2.1. Timestamp
ts = fread(fileID, nSampBase, 'float64');
ts = reshape(ts, nSampBase, 1);
signals.timestamp = struct('data', ts, 'fs', fsBase);
% 2.2. Signals data
signalNames = fieldnames(signals);
for i = 1:numel(signalNames)
    sigName = signalNames{i};
    sigData = signals.(sigName);

    if strcmp(sigName, 'timestamp')
        continue;
    end

    nSamp = sigData.nSamp;
    nCh = sigData.nCh;
    signals.(sigName) = rmfield(sigData, {'nSamp', 'nCh'});
    data = fread(fileID, nSamp * nCh, 'float32');
    data = reshape(data, [nCh, nSamp])';
    signals.(sigName).data = data;
end
% 2.3. Trigger (optional)
if isTrigger
    trigger = fread(fileID, nSampBase, 'uint32');
    trigger = reshape(trigger, nSampBase, 1);
    signals.trigger = struct('data', trigger, 'fs', fsBase);
end
%nCh = fread(fileID, 1, 'uint32');
%data = fread(fileID, 'float32');
%mg = reshape(data, nCh, []);
fclose('all');
end