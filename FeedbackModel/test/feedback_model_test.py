"""
Test of the feedback model.
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.io

import bciutils

if __name__ == "__main__":
    # Load reference variables
    reference_variables = scipy.io.loadmat('variables_ref.mat')
    eeg = reference_variables['eeg']
    n_samples, n_channels = np.shape(eeg)

    sample_rate = 128
    s_rate_half = sample_rate / 2

    # Define bandpass for classification unit
    order = 12
    fstop = [3, 35]
    fpass = [8, 30]
    fstop = [freq / s_rate_half for freq in fstop]
    fpass = [freq / s_rate_half for freq in fpass]
    bandpass_cl = bciutils.Bandpass(order=order, fstop=fstop, fpass=fpass,
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
                                bandpass_erds=None,
                                csp=csp_filter, lda=lda_coef, log_band_power=log_band_power_unit)

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
    class_label_ref = reference_variables['class_label']
    distance_ref = reference_variables['distance']

    plt.figure(1)
    plt.plot(class_label_arr, 'b')
    plt.plot(class_label_ref, 'r--')
    plt.title('Class label')
    plt.show()

    plt.figure(2)
    plt.plot(distance_arr, 'b')
    plt.plot(distance_ref, 'r--')
    plt.title('Distance')
    plt.show()
