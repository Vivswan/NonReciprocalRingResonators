function [Q, peak_idx] = getQ(signal, lambda)
    % find peaks
    [~, peak_idx] = findpeaks(abs(signal));
    lambda_res = lambda(peak_idx);
    
    % find FWHM at 3dB points
    [~, FWHM_idx] = findpeaks(-abs(signal + 3));
    FWHM = lambda(FWHM_idx(1:2:end)) - lambda(FWHM_idx(2:2:end));
    
    % Quality Factor
    Q = lambda_res./FWHM;
    
    % plot(lambda, signal, 'r-', lambda(peak_idx), signal(peak_idx), 'bo', lambda(FWHM_idx), signal(FWHM_idx), 'bx')
end