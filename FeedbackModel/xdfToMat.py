import json
import numpy as np
import os
import pyxdf
import scipy.io


def load_xdf(file_name, lsl_config):
    streams, fileheader = pyxdf.load_xdf(file_name)
    streams_info = []

    for stream in streams:
        streams_info.append(stream['info']['name'][0])

    streams_info = np.array(streams_info)

    eeg_pos = np.where(streams_info == lsl_config['eeg']['name'])[0][0]
    marker_pos = np.where(streams_info == lsl_config['marker']['name'])[0][0]

    return streams[eeg_pos], streams[marker_pos]


def add_class_labels_to_eeg(stream_eeg, stream_marker):
    eeg_time = stream_eeg['time_stamps']
    marker_series = np.array(stream_marker['time_series'])
    cue_times = (stream_marker['time_stamps'])[np.where(marker_series == 'Cue')[0]]

    conditions = marker_series[np.where(np.char.find(marker_series[:, 0], 'Start_of_Trial') == 0)[0]]
    conditions[np.where(conditions == 'Start_of_Trial_l')] = 121
    conditions[np.where(conditions == 'Start_of_Trial_r')] = 122

    cue_positions = np.zeros((np.shape(eeg_time)[0], 1), dtype=int)
    for t, c in zip(cue_times, conditions):
        pos = find_nearest_index(eeg_time, t)
        cue_positions[pos] = c

    return np.append(cue_positions, stream_eeg['time_series'], axis=1)


def find_nearest_index(array, value):
    idx = np.searchsorted(array, value, side="right")
    if idx == len(array):
        return idx - 1
    else:
        return idx


def save_to_mat(file_path, data):
    if os.path.isfile(file_path):
        data_old = scipy.io.loadmat(mat_file_path)['data']
        data = np.append(data_old, data, axis=0)

    scipy.io.savemat(mat_file_path, {'data': data})


if __name__ == "__main__":
    directory = 'data/recordings/sub-P001/ses-S002/eeg/'
    xdf_file_path = directory + 'sub-P001_ses-S002_task-Default_run-001_eeg.xdf'
    mat_file_path = directory + 'messung.mat'

    cwd = os.getcwd()
    config_file = cwd + '/../bci-config.json'

    # Read BCI Configuration
    with open(config_file) as json_file:
        config = json.load(json_file)

    eeg_stream, marker_stream = load_xdf(xdf_file_path, config['general-settings']['lsl-streams'])
    eeg_and_label = add_class_labels_to_eeg(eeg_stream, marker_stream)
    save_to_mat(mat_file_path, eeg_and_label)
