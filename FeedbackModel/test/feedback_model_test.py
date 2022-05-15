"""
Test of the feedback model.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.io

import bciutils

if __name__ == "__main__":
    # Load reference eeg signal
    eeg = scipy.io.loadmat('eeg.mat')['eeg']
    n_samples, n_channels = np.shape(eeg)

    cwd = os.getcwd()
    config_file = cwd + '/../../bci-config.json'

    # Read BCI Configuration
    with open(config_file) as json_file:
        config = json.load(json_file)

    sample_rate = config['eeg-settings']['sample-rate']
    s_rate_half = config['eeg-settings']['sample-rate'] / 2

    # Define bandpass for classification unit
    bandpass_settings_cl = config['feedback-model-settings']['bandpass']
    fstop = [freq / s_rate_half for freq in bandpass_settings_cl['fstop']]
    fpass = [freq / s_rate_half for freq in bandpass_settings_cl['fpass']]
    bandpass_cl = bciutils.Bandpass(order=bandpass_settings_cl['order'], fstop=fstop, fpass=fpass,
                                    n=n_channels)

    # Define bandpass for ERDS unit
    bandpass_settings_erds = config['feedback-model-settings']['bandpass-erds']
    fstop_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fstop']]
    fpass_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fpass']]
    bandpass_erds = bciutils.Bandpass(order=bandpass_settings_erds['order'], fstop=fstop_erds, fpass=fpass_erds,
                                      n=n_channels)

    # Load CSP and LDA coefficients
    csp_filter = scipy.io.loadmat('csp.mat')['csp_filters']
    lda_coef = scipy.io.loadmat('lda.mat')['W']

    # Define log band power unit
    log_band_power_unit = bciutils.LogBandPower(window_length=1 * sample_rate,
                                                n=np.shape(csp_filter)[0])

    # Define BCI Core
    bci_core = bciutils.BCICore(sample_rate=sample_rate,
                                bandpass_cl=bandpass_cl,
                                bandpass_erds=bandpass_erds,
                                csp=csp_filter, lda=lda_coef, log_band_power=log_band_power_unit)

    # Feed bandpass filter
    for i in range(sample_rate * 3):
        sample = np.expand_dims(eeg[i, :], axis=0)
        bci_core.bandpass_cl.bandpass_filter(sample)

    class_label_list = []
    distance_list = []
    # Classify sample by sample
    for i in range(n_samples):
        sample = np.expand_dims(eeg[i, :], axis=0)
        y_bp = bci_core.bandpass_cl.bandpass_filter(sample)
        y_csp = bci_core.csp_filter(y_bp)
        y_lbp = bci_core.log_band_power.compute_log_band_power(y_csp)

        label, distance = bci_core.lda_predict(y_lbp)
        class_label_list.append(label)
        distance_list.append(distance)

    class_label_arr = np.array(class_label_list)
    distance_arr = np.array(distance_list)

    # Compare to Graz BCI model
    class_label_ref = scipy.io.loadmat('class_label.mat')['class_label']
    distance_ref = scipy.io.loadmat('distance.mat')['distance']

    plt.figure(1)
    plt.plot(class_label_arr, 'b')
    plt.plot(class_label_ref, 'k')
    plt.title('Class label')
    plt.show()

    plt.figure(2)
    plt.plot(distance_arr, 'b')
    plt.plot(distance_ref, 'k')
    plt.title('Distance')
    plt.show()

    print('hello')
