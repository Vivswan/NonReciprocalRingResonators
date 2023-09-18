clear;
close all;

using_Q = 10000;

load("simulation_3_non_reciprocal.mat");
lambdaNR = 1e6 * 3e8./frequencies;
phaseNR = phase;
Diff_T_NR = zeros(length(phaseNR), length(lambdaNR));

Qs = zeros(length(coupling), 1);
for i = 2:length(coupling)
    [Q, ~] = getQ(squeeze(signal_1(i, 1, :)), lambdaNR);
    Qs(i) = mean(Q);
end
[~, c_idx] = min(abs(Qs - using_Q));
disp(['coupling = ', num2str(coupling(c_idx + 1)), ', Q = ', num2str(Qs(c_idx + 1))]);
disp(['coupling = ', num2str(coupling(c_idx)), ', Q = ', num2str(Qs(c_idx))]);
disp(['coupling = ', num2str(coupling(c_idx - 1)), ', Q = ', num2str(Qs(c_idx - 1))]);

% Find resonance frequency at zero phase shift
[~, peak1_idx] = getQ(squeeze(signal_1(c_idx, floor(length(phase)/2), :)), lambdaNR);
[~, peak2_idx] = getQ(squeeze(signal_2(c_idx, floor(length(phase)/2), :)), lambdaNR);
lambda0_NR = lambdaNR(round(mean(peak1_idx(end), peak2_idx(end))));
[~, NR_idx] = min(abs(lambdaNR - 1.548245)); % 1.548245, 1.54828

figure;
subplot(2,2,[1,3]);
hold on;
for i = 1:length(phase)
    % disp(['coupling = ',num2str(coupling(c_idx)),', phase = ', num2str(phase(i))]);
    this_signal_1 = squeeze(signal_1(c_idx, i, :));
    this_signal_2 = squeeze(signal_2(c_idx, i, :));

    plot(lambdaNR - lambda0_NR, this_signal_1 - 30*(i-1), 'r-', lambdaNR - lambda0_NR, this_signal_2 - 30*(i-1), 'b-');

    Diff_T_NR(i,:) = 10.^(this_signal_2/10) - 10.^(this_signal_1/10);
    [~, peak_idx] = getQ(this_signal_2, lambdaNR);
    peak_array_NR(i) = peak_idx(end);
end
xlim([-1.2e-3, 1.2e-3]);
xlabel('Wavelength (um)');
ylabel('Transmission');
legend({'Through Port (CW)', 'Through Port (CCW)'});
title('Non-Reciprocal MRR');
line([lambdaNR(NR_idx) - lambda0_NR, lambdaNR(NR_idx) - lambda0_NR],[0, -2000], 'Color','black','LineStyle','--', 'LineWidth', 1.5);

load("simulation_3_reciprocal.mat");
lambdaR = 1e6 * 3e8./frequencies;
phaseR = phase;
Diff_T_R = zeros(length(phaseR), length(lambdaR));

[~, peak_idx] = getQ(squeeze(signal_1(c_idx, 1, :)), lambdaR);
R_idx = peak_idx(end);
lambda0_R = lambdaR(R_idx);

subplot(2,2,[2,4]);
hold on;
for i = 1:length(phase)
    % disp(['coupling = ',num2str(coupling(c_idx)),', phase = ', num2str(phase(i))]);
    this_signal_1 = squeeze(signal_1(c_idx, i, :));
    this_signal_2 = squeeze(signal_2(c_idx, i, :));

    plot(lambdaR - lambda0_R, this_signal_1 - 30*(i-1), 'r-', lambdaR - lambda0_R, this_signal_2 - 30*(i-1), 'b-');
    Diff_T_R(i,:) = 10.^(this_signal_2/10) - 10.^(this_signal_1/10);
end
xlim([-0.2e-3, 2.2e-3]);
xlabel('Wavelength (um)');
ylabel('Transmission');
title('Reciprocal MRR');
legend({'Through Port', 'Drop Port'});
line([lambdaR(R_idx) - lambda0_R, lambdaR(R_idx) - lambda0_R],[0, -2000], 'Color','black','LineStyle','--', 'LineWidth', 1.5);


s = linspace(0,1,100);
rgb1 = [0.230, 0.299, 0.754];
rgb2 = [0.706, 0.016, 0.150];
[map] = diverging_map(s,rgb1,rgb2);

load("simulation_3_non_reciprocal.mat");
figure;
colormap(map);
contourf(lambdaNR - lambda0_NR, phaseNR/pi, Diff_T_NR, 64, 'Linestyle','None');
caxis([-1, 1]);
colorbar;
xlim([-1.2e-3, 1.2e-3]);
xlabel('Wavelength (um)');
ylabel('Phase shift (rad/\pi)');
title('Differential Transmission (Non-Reciprocal)');

figure;
plot(phaseNR/pi, Diff_T_NR(:, peak_array_NR(20:2:32)));
xlim([-0.5, 0.5]);
xlabel('Phase shift (rad/\pi)');
ylabel('Differential Transmission');
title('Differential Transmission (Non-Reciprocal)');

figure;
colormap(map);
contourf(lambdaR - lambda0_R, phaseR/pi, Diff_T_R, 64, 'Linestyle','None');
caxis([-1, 1]);
colorbar;
xlim([-0.2e-3, 2.2e-3]);
xlabel('Wavelength (um)');
ylabel('Phase shift (rad/\pi)');
title('Differential Transmission (Reciprocal)');

% High res transmission difference
load("simulation_3_reciprocal.mat");
signal_1_cIdx = squeeze(signal_1(c_idx, 1, :));
signal_2_cIdx = squeeze(signal_2(c_idx, 1, :));

[~, peak_idx] = getQ(signal_1_cIdx, lambdaR);
phase_from_lambda = 2*(lambdaR - lambda0_R)/abs(diff(lambdaR(peak_idx)));
dT_R = 10.^(signal_2_cIdx/10) - 10.^(signal_1_cIdx/10);

figure;
subplot(211);
plot(phase_from_lambda, squeeze(signal_1_cIdx), 'r-', phase_from_lambda, signal_2_cIdx, 'b-');
xlim([-1, 3]);
xlabel('Phase shift (rad/\pi)');
ylabel('Transmission (dB)');

subplot(212);
plot(phase_from_lambda, dT_R);
xlim([0, 1]);
xlabel('Phase shift (rad/\pi)');
ylabel('Differential Transmission');
