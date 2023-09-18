clear;
close all;

% 5 for Q = 10000
% 5 for Q = 15000
filename = "simulation_5_non_reciprocal.mat";

% Find resonance frequency at zero phase shift
load(filename);
lambdaNR = 1e6 * 3e8./frequencies;
phaseNR = phase / pi;

[~, p_idx] = min(abs(phaseNR - 0.5));
signal_1_p_idx = squeeze(signal_1(1, p_idx, :));

[~, peak_idx] = getQ(signal_1_p_idx, lambdaNR);
peak_idx = peak_idx(round(numel(peak_idx)/2));

signal_1_probe = squeeze(signal_1(1, :, peak_idx));
signal_2_probe = squeeze(signal_2(1, :, peak_idx));

figure;
subplot(211)
plot(phaseNR, signal_1_probe, 'r-', phaseNR, signal_2_probe, 'b-')
xlabel('Phase shift (rad/\pi)')
ylabel('Transmission (dB)')


load(filename);
lambdaNR = 1e6 * 3e8./frequencies;
phaseNR = phase / pi;

[~, p_idx] = min(abs(phaseNR));
signal_1_p_idx = squeeze(signal_1(1, p_idx, :));

[~, peak_idx] = getQ(signal_1_p_idx, lambdaNR);
peak_idx = peak_idx(round(numel(peak_idx)/2));

[~, FWHM_idx] = findpeaks(-abs(signal_1_p_idx + 3));

subplot(212);
hold on;
for i = 1:3
    probe_idx = (FWHM_idx - peak_idx) * i;
    probe_idx = peak_idx + min(probe_idx(probe_idx > 0));
    a = squeeze(signal_1(1, :, probe_idx));
    b = squeeze(signal_2(1, :, probe_idx));
    dT_R = 10.^(a/10) - 10.^(b/10);

    plot(phaseNR, dT_R);
end
xlim([-0.25, 0.25]);
xlabel('Phase shift (rad/\pi)');
ylabel('Differential Transmission');
