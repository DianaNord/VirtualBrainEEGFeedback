# ----------------------------------------------------------------------------------------------------------------------
# Calculates CSP and LDA
# ----------------------------------------------------------------------------------------------------------------------
import json
import os
import scipy.io

from bci_modules import CSPAndLDA

if __name__ == "__main__":

    modality = 'MI'
    subject_id = 'sub-P002'

    cwd = os.getcwd()
    root_dir = cwd + '/data/current/'
    dir_in = root_dir + subject_id + '/' + modality + '/'
    dir_out = dir_in + '../'
    file_path = dir_in + 'messung.mat'

    config_file_name = '/../bci-config.json'
    config_file = cwd + config_file_name

    # load bci configuration
    with open(config_file) as json_file:
        config = json.load(json_file)

    data_mat = scipy.io.loadmat(file_path)['data'].T
    labels = data_mat[0, :]
    eeg = data_mat[1:, :]

    csp_lda_obj = CSPAndLDA(eeg=eeg, labels=labels, bci_config=config)
    csp_lda_obj.compute_csp(output_path=dir_out)
    csp_lda_obj.compute_lda(output_path=dir_out)
