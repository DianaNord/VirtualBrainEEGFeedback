# ----------------------------------------------------------------------------------------------------------------------
# EEG Feedback Model
# performs classification and calculates erds-values for online-BCIs
# ----------------------------------------------------------------------------------------------------------------------
import json
import numpy as np
import os
import scipy.io

import bci_modules

if __name__ == "__main__":

    cwd = os.getcwd()
    config_file = cwd + '/../bci-config.json'

    # Read BCI Configuration
    with open(config_file) as json_file:
        config = json.load(json_file)

    # Initialize the bci model
    bci_model = bci_modules.BCI(config)

    # Load CSP and LDA filter
    csp_filter = scipy.io.loadmat('data/CSP_LDA/csp.mat')['csp_filter']
    lda = scipy.io.loadmat('data/CSP_LDA/lda.mat')['W']

    s_rate_half = bci_model.sample_rate / 2

    # Define bandpass unit
    bandpass_settings = config['feedback-model-settings']['bandpass']
    fstop = [freq / s_rate_half for freq in bandpass_settings['fstop']]
    fpass = [freq / s_rate_half for freq in bandpass_settings['fpass']]
    bandpass_definitons = bci_modules.Bandpass(order=bandpass_settings['order'], fstop=fstop, fpass=fpass,
                                               n=bci_model.n_enabled_channels)

    bandpass_settings_erds = config['feedback-model-settings']['bandpass-erds']
    fstop_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fstop']]
    fpass_erds = [freq / s_rate_half for freq in bandpass_settings_erds['fpass']]
    bandpass_ref = bci_modules.Bandpass(order=bandpass_settings_erds['order'], fstop=fstop_erds, fpass=fpass_erds,
                                        n=bci_model.n_enabled_channels)

    # Define log band power unit
    log_band_power_definitions = bci_modules.LogBandPower(window_length=1 * bci_model.sample_rate,
                                                          n=np.shape(csp_filter)[0])

    # Define bci core
    bci_model.bci_core = bci_modules.BCICore(sample_rate=bci_model.sample_rate,
                                             bandpass=bandpass_definitons,
                                             bandpass_ref=bandpass_ref,
                                             csp=csp_filter, log_band_power=log_band_power_definitions, lda=lda)

    bci_model.start_feedback_loop()
