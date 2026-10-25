%% Phase Detector Test (9/16/26) - compare output vs. frequency across TX power levels
% Reads the side-by-side blocks in "Phase Detector Test  9_16_26.csv" and
% overlays one line per TX power / attenuation setting.

clear; close all;

csvPath = fullfile('C:\ThatFamily Dropbox\Sorin Jayaweera\allSaves\mudd\senior\clinic\data', ...
                   'Phase Detector Test  9_16_26.csv');

raw = readcell(csvPath, 'Delimiter', ',');
isText = @(c) ischar(c) || isstring(c);

% Locate each block by its "TX Power dBm = ..." title and its "Input Frequency" header
[titleRow, titleCol] = find(cellfun(@(c) isText(c) && contains(c, 'TX Power'), raw));
[hdrRow,   freqCol]  = find(cellfun(@(c) isText(c) && contains(c, 'Input Frequency'), raw));
[titleCol, order] = sort(titleCol); titleRow = titleRow(order);
[freqCol,  order] = sort(freqCol);  hdrRow   = hdrRow(order);

firstDataRow = max(hdrRow) + 2;   % skip the "Trial 1 / Trial 2" row

% Data ends before the first row containing text (the "Lowest Power ..." summary)
hasText = any(cellfun(@(c) isText(c) && strlength(strtrim(string(c))) > 0, raw), 2);
textRow = find(hasText & (1:size(raw,1))' >= firstDataRow, 1);
if isempty(textRow), lastDataRow = size(raw, 1); else, lastDataRow = textRow - 1; end

blocks = struct('label', {}, 'txPower', {}, 'freq', {}, 'trial1', {}, 'trial2', {});
for k = 1:numel(freqCol)
    % Title for this block = nearest title at or left of the frequency column
    idx   = find(titleCol <= freqCol(k), 1, 'last');
    label = strtrim(string(raw{titleRow(idx), titleCol(idx)}));

    fc = freqCol(k);
    f  = cellToNum(raw(firstDataRow:lastDataRow, fc));
    t1 = cellToNum(raw(firstDataRow:lastDataRow, fc + 1));
    t2 = cellToNum(raw(firstDataRow:lastDataRow, fc + 2));

    keep = ~isnan(f) & (~isnan(t1) | ~isnan(t2));
    [f, order] = sort(f(keep));
    t1 = t1(keep); t1 = t1(order);
    t2 = t2(keep); t2 = t2(order);

    blocks(k).label   = label;
    blocks(k).txPower = str2double(regexp(label, '-?\d+(\.\d+)?', 'match', 'once'));
    blocks(k).freq    = f;
    blocks(k).trial1  = t1;
    blocks(k).trial2  = t2;
end

%% Plot
figure('Name', 'Phase Detector Test 9/16/26', 'Color', 'w');
hold on; grid on; box on;
colors = lines(numel(blocks));

for k = 1:numel(blocks)
    b  = blocks(k);
    m1 = ~isnan(b.trial1);
    plot(b.freq(m1), b.trial1(m1), '-o', 'Color', colors(k,:), 'LineWidth', 1.5, ...
         'MarkerFaceColor', colors(k,:), 'MarkerSize', 4, ...
         'DisplayName', sprintf('TX = %g dBm', b.txPower));

    m2 = ~isnan(b.trial2);
    if any(m2)
        plot(b.freq(m2), b.trial2(m2), '--s', 'Color', colors(k,:), 'LineWidth', 1.2, ...
             'MarkerSize', 4, 'DisplayName', sprintf('TX = %g dBm (Trial 2)', b.txPower));
    end
end

xlabel('Input Frequency (GHz)');
ylabel('Output Voltage (mW)');   % unit as labeled in the CSV
title('Phase Detector Output vs. Frequency by TX Power');
legend('Location', 'northwest');
hold off;

%% Summary: min / max / amplitude for each setting
fprintf('\n%-14s %10s %10s %10s %10s %10s\n', 'TX Power', 'Min', 'f@Min', 'Max', 'f@Max', 'A');
for k = 1:numel(blocks)
    b = blocks(k);
    [vMin, iMin] = min(b.trial1);
    [vMax, iMax] = max(b.trial1);
    fprintf('%-14s %10.2f %10.3f %10.2f %10.3f %10.2f\n', sprintf('%g dBm', b.txPower), ...
            vMin, b.freq(iMin), vMax, b.freq(iMax), (vMax - vMin));
end

%% Helpers
function v = cellToNum(c)
    v = nan(numel(c), 1);
    for i = 1:numel(c)
        x = c{i};
        if isnumeric(x) && isscalar(x)
            v(i) = double(x);
        elseif ischar(x) || isstring(x)
            v(i) = str2double(x);
        end
    end
end
