# ----------------------------------------------------------------------------------------------------------------------
# Calculates CSP and LDA
# ----------------------------------------------------------------------------------------------------------------------
import json
import os
import scipy.io
import fnmatch
import numpy as np

from bci_modules import CSPAndLDA

if __name__ == "__main__":
    directory = 'data/recordings/current/mat-files/'
    directory_out = directory + '../'
    config_file_name = '/../bci-config.json'

    cwd = os.getcwd()
    config_file = cwd + config_file_name

    # load bci configuration
    with open(config_file) as json_file:
        config = json.load(json_file)

    eeg = []
    labels = []
    file_list = []
    for path, folders, files in os.walk(directory):
        for file in files:
            if fnmatch.fnmatch(file, '*.mat'):
                file_list.append(os.path.join(path, file))

    first_file = True
    for file in file_list:
        data_mat = scipy.io.loadmat(file)['data'].T
        if first_file:
            labels = data_mat[0, :]
            eeg = data_mat[1:, :]
        else:
            labels = np.append(labels, data_mat[0, :])
            eeg = np.append(eeg, data_mat[1:, :], axis=1)

        first_file = False

    csp_lda_obj = CSPAndLDA(eeg=eeg, labels=labels, bci_config=config)
    csp_lda_obj.compute_csp(output_path=directory_out)
    csp_lda_obj.compute_lda(output_path=directory_out)
