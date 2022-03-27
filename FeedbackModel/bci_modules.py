# ----------------------------------------------------------------------------------------------------------------------
# Includes all classes needed for performing online eeg analyis
# ----------------------------------------------------------------------------------------------------------------------
from enum import Enum
import math
import numpy as np
from pylsl import StreamInfo, StreamInlet, StreamOutlet, resolve_stream, local_clock
import scipy.io
from scipy import signal, linalg
import threading


class BCIState(Enum):
    START = 0
    REFERENCE = 1
    CUE = 2
    FEEDBACK = 3
    BREAK = 4
    SLEEP = 5


class ERDSMode(str, Enum):
    AVERAGE = 'average'
    SINGLE = 'single'


class BCI:
    def __init__(self, bci_config):
        self.state = BCIState.START
        self.bci_core = None

        self.stream_eeg = bci_config['general-settings']['lsl-streams']['eeg']
        self.stream_marker = bci_config['general-settings']['lsl-streams']['marker']
        self.inlet_eeg: None

        self.stream_fb_cl = bci_config['general-settings']['lsl-streams']['fb-lda']
        self.stream_fb_erds = bci_config['general-settings']['lsl-streams']['fb-erds']

        self.thread_classification = threading.Thread(target=self.__compute_classification)
        self.thread_erds = threading.Thread(target=self.__compute_erds)
        self.thread_marker = threading.Thread(target=self.start_feedback_loop)

        self.sample_rate = 0
        self.idx_start_ref = 0
        self.n_enabled_channels = 0
        self.idx_enabled_channels = 0
        self.channel_to_roi_map = []
        self.n_roi = bci_config['feedback-model-settings']['erds']['number-roi']

        self.data_ref = None
        self.data_ref_mean = None

        self.__resolve_eeg_stream()
        self.__select_enabled_channels(bci_config['eeg-settings']['channels'],
                                       bci_config['feedback-model-settings']['erds'])

    def __del__(self):
        if self.thread_erds.is_alive():
            self.thread_erds.join()
        if self.thread_classification.is_alive():
            self.thread_classification.join()
        if self.thread_marker.is_alive():
            self.thread_marker.join()

    def __resolve_eeg_stream(self):
        self.inlet_eeg = self.resolve_lsl_stream(name=self.stream_eeg['name'])

        info_eeg = self.inlet_eeg.info()
        print(info_eeg.as_xml())

        self.n_enabled_channels = int(info_eeg.channel_count())
        self.sample_rate = int(info_eeg.nominal_srate())
        self.idx_start_ref = int(info_eeg.nominal_srate() / 2)

    def __select_enabled_channels(self, channel_settings, erds_settings):
        list_is_channel_enabled = np.zeros((self.n_enabled_channels,), dtype=bool)
        list_roi_of_channel = np.zeros((self.n_enabled_channels,), dtype=int)
        list_id_of_channel = np.zeros((self.n_enabled_channels,), dtype=int)

        cnt = 0
        for ch in channel_settings:
            obj = channel_settings[ch]
            list_is_channel_enabled[cnt] = obj['enabled']
            list_roi_of_channel[cnt] = obj['roi']
            list_id_of_channel[cnt] = obj['id']
            cnt += 1

        self.idx_enabled_channels = np.where(list_is_channel_enabled)[0]
        self.n_enabled_channels = np.shape(self.idx_enabled_channels)[0]

        list_roi_of_channel = list_roi_of_channel[self.idx_enabled_channels]
        list_id_of_channel = list_id_of_channel[self.idx_enabled_channels]

        if erds_settings['mode'] == ERDSMode.AVERAGE:
            for roi in range(1, self.n_roi + 1):
                self.channel_to_roi_map.append(np.where(list_roi_of_channel == roi)[0])
        elif erds_settings['mode'] == ERDSMode.SINGLE:
            for ch in erds_settings['single-mode-channels']:
                self.channel_to_roi_map.append(np.where(list_id_of_channel == ch)[0])

    def __reset_erds(self):
        self.data_ref = np.zeros((1, self.n_enabled_channels))
        self.data_ref_mean = np.zeros((1, self.n_enabled_channels))
        self.data_ref_mean[:] = np.nan

    def __compute_erds(self):
        # important that this thread has its own instance of inlet eeg
        inlet_eeg = self.resolve_lsl_stream(name=self.stream_eeg['name'])

        stream_info = StreamInfo(name=self.stream_fb_erds['name'], channel_count=self.n_roi, nominal_srate=0,
                                 channel_format='float32', source_id=self.stream_fb_erds['id'])
        outlet_fb_erds = StreamOutlet(stream_info)

        self.__reset_erds()
        erds_per_roi = np.zeros((self.n_roi,))

        while True:
            sample, timestamp = inlet_eeg.pull_sample()
            sample = np.expand_dims(sample, axis=0)[:, self.idx_enabled_channels]

            if self.state == BCIState.REFERENCE:
                self.data_ref = np.append(self.data_ref, np.square(self.bci_core.bandpass_ref.bandpass_filter(sample)),
                                          axis=0)
            elif self.state == BCIState.FEEDBACK:
                erds_a = np.square(self.bci_core.bandpass_ref.bandpass_filter(sample))

                # This can happen if the state changed to BCIState.BREAK in the meantime
                if np.any(np.isnan(erds_a)) or np.any(np.isnan(
                        self.data_ref_mean)):
                    continue

                erds = np.divide(-(self.data_ref_mean - erds_a), self.data_ref_mean)

                # mean erds over roi
                for roi in range(self.n_roi):
                    erds_per_roi[roi] = np.mean(erds[0, self.channel_to_roi_map[roi]])

                outlet_fb_erds.push_sample(erds_per_roi, local_clock())
            elif self.state == BCIState.START:
                self.bci_core.bandpass_ref.bandpass_filter(sample)

    def __compute_classification(self):
        stream_info = StreamInfo(name=self.stream_fb_cl['name'], channel_count=2, nominal_srate=0,
                                 channel_format='float32', source_id=self.stream_fb_cl['id'])
        outlet_fb_cl = StreamOutlet(stream_info)

        while True:
            sample, timestamp = self.inlet_eeg.pull_sample()
            sample = np.expand_dims(sample, axis=0)[:, self.idx_enabled_channels]

            if self.state == BCIState.FEEDBACK:
                y_bp = self.bci_core.bandpass.bandpass_filter(sample)
                y_csp = self.bci_core.apply_csp(y_bp)
                y_lbp = self.bci_core.log_band_power.compute_log_band_power(y_csp)

                label, distance = self.bci_core.classification(y_lbp)
                outlet_fb_cl.push_sample([label[0] - 1, distance[0]], local_clock())
            elif self.state == BCIState.START:
                self.bci_core.bandpass.bandpass_filter(sample)

    def start_feedback_loop(self):

        inlet_marker = self.resolve_lsl_stream(name=self.stream_marker['name'])

        self.thread_classification.start()
        self.thread_erds.start()

        # Feed bandpass filter with a few samples
        start_time = local_clock()
        while self.state == BCIState.START:
            if int(local_clock() - start_time) > 3:
                self.state = BCIState.SLEEP

        while True:
            if inlet_marker is None:
                continue
            marker, timestamp = inlet_marker.pull_sample()
            if marker is None:
                continue

            if marker[0] == 'Reference':
                self.state = BCIState.REFERENCE
            elif marker[0] == 'Cue':
                self.state = BCIState.CUE
                # Calculate mean erds values over reference period
                if np.shape(self.data_ref)[0] > 1:
                    self.data_ref_mean = np.mean(np.delete(self.data_ref, 0, 0)[self.idx_start_ref:, :],
                                                 axis=0)
                else:
                    print("ERROR no ERDS values are calculated")
            elif marker[0] == 'Feedback':
                self.state = BCIState.FEEDBACK
            elif marker[0] == 'End_of_Trial':
                self.state = BCIState.BREAK
                self.bci_core.set_lda_distance_parameters()
                self.__reset_erds()

    @staticmethod
    def resolve_lsl_stream(name):
        stream = resolve_stream("name", name)
        inlet = StreamInlet(stream[0])
        return inlet


class BCICore:
    def __init__(self, sample_rate, bandpass, bandpass_ref, csp, log_band_power, lda):
        self.sample_rate = sample_rate
        self.bandpass = bandpass
        self.bandpass_ref = bandpass_ref
        self.CSP = csp
        self.log_band_power = log_band_power
        self.LDA = lda

        self.label = None
        self.label_buffer = None
        self.is_class_buffer = None
        self.cnt_sample = 0

        self.set_lda_distance_parameters()

        np.seterr(invalid='ignore')  # ignores inf values (in matmul() in classification())
        np.seterr(divide='ignore')  # ignores division by zero (happens in log_band_power())

    def set_lda_distance_parameters(self):
        self.label_buffer = np.zeros((self.sample_rate,), dtype=int)
        self.is_class_buffer = np.zeros((2,), dtype=int)
        self.cnt_sample = 0

    def apply_csp(self, x):
        return np.matmul(x, self.CSP.T)

    def classification(self, x):
        x_conc = np.append(np.ones([np.shape(x)[0], 1]), x, axis=1)
        x_mat = np.matmul(x_conc, self.LDA.T)
        linear_scores = np.divide(np.multiply(x_mat, 100),
                                  np.max(np.abs(x_mat)))
        self.label = np.nanargmax(linear_scores, axis=1) + 1
        label, distance = self.lda_disctance_calculation()

        return label, distance

    def lda_disctance_calculation(self):
        # linear distance function
        # distance equals length of feedback bar -> in VR intesity of outline glow
        is_class_1 = 1 * (self.label == 1) - 1 * (self.label_buffer[self.cnt_sample] == 1) + self.is_class_buffer[0]
        is_class_2 = 1 * (self.label == 2) - 1 * (self.label_buffer[self.cnt_sample] == 2) + self.is_class_buffer[1]
        class_label = np.argmax([is_class_1, is_class_2], axis=0) + 1

        distance = self.is_class_buffer[class_label - 1] / self.sample_rate

        self.label_buffer[self.cnt_sample] = self.label
        self.is_class_buffer = np.array([is_class_1, is_class_2])

        if self.cnt_sample < self.sample_rate - 1:
            self.cnt_sample += 1
        else:
            self.cnt_sample = 0

        return class_label, distance

    @staticmethod
    def calculate_accuracy(values, values_ref):
        cnt = 0
        n = len(values_ref)
        for v in range(n):
            if values[v] == values_ref[v]:
                cnt += 1
        return cnt / n


class Bandpass:
    def __init__(self, order, fstop, fpass, n):
        self.order = order
        self.fstop = fstop
        self.fpass = fpass
        self.n = n
        self.sos = None
        self.zi0 = None
        self.zi = None

        self.__init_filter()

    def __init_filter(self):
        self.sos = signal.iirfilter(self.order / 2, self.fpass, btype='bandpass', ftype='butter',
                                    output='sos')

        zi = signal.sosfilt_zi(self.sos)

        if self.n > 1:
            zi = np.tile(zi, (self.n, 1, 1)).T
        self.zi0 = zi.reshape((np.shape(self.sos)[0], 2, self.n))
        self.zi = self.zi0

    def reset_zi(self):
        self.zi = self.zi0

    def bandpass_filter(self, x):
        y, self.zi = signal.sosfilt(self.sos, x, zi=self.zi, axis=0)
        return y


class LogBandPower:
    def __init__(self, window_length, n):
        self.window_length = window_length
        self.n = n
        self.a = None
        self.b = None
        self.zi = None

        self.__init_conditions()

    def __init_conditions(self):
        window_samples = math.floor(self.window_length)
        self.b = 1 / window_samples * np.ones((1, window_samples))
        self.a = 1

        zi = signal.lfilter_zi(self.b[0], self.a)
        if self.n > 1:
            zi = np.tile(zi, (self.n, 1)).T
        self.zi = zi

    def compute_log_band_power(self, x):
        x_filt, self.zi = signal.lfilter(self.b[0], self.a, np.square(np.abs(x)), zi=self.zi, axis=0)

        return np.log10(x_filt)


class CSPAndLDA:
    def __init__(self, eeg, labels, bci_config):
        self.eeg = eeg
        self.labels = labels
        self.n_channels = None
        self.pos_class_1 = np.where(self.labels == 121)[0]
        self.pos_class_2 = np.where(self.labels == 122)[0]
        self.n_trials = [len(self.pos_class_1), len(self.pos_class_2)]
        self.sample_rate = bci_config['eeg-settings']['sample-rate']
        self.channel_settings = bci_config['eeg-settings']['channels']

        self.bp_frequency = bci_config['feedback-model-settings']['bandpass']['fpass']
        self.bp_order = bci_config['feedback-model-settings']['bandpass']['order-offline']

        self.d_cue = bci_config['general-settings']['timing']['duration-cue']
        self.d_task = bci_config['general-settings']['timing']['duration-task']

        self.csp_filter = None
        self.lda_coefficients = None

        self.__select_channels()
        self.__bandpass()

    def __select_channels(self):
        list_is_channel_enabled = np.zeros((np.shape(self.eeg)[0],), dtype=bool)

        cnt = 0
        for ch in self.channel_settings:
            obj = self.channel_settings[ch]
            list_is_channel_enabled[cnt] = obj['enabled']
            cnt += 1

        self.eeg = self.eeg[np.where(list_is_channel_enabled)[0]]
        self.n_channels = np.shape(self.eeg)[0]

    def __extract_epochs(self):
        n_cue = int(np.floor(self.sample_rate * self.d_cue))
        n_samples = n_cue + int(np.floor(self.sample_rate * self.d_task))
        class_1, class_2 = np.array([]), np.array([])

        for i in range(self.n_trials[0]):
            if i == 0:
                class_1 = self.eeg[:, self.pos_class_1[i] + n_cue:self.pos_class_1[i] + n_samples]
            else:
                class_1 = np.append(class_1, self.eeg[:, self.pos_class_1[i] + n_cue:self.pos_class_1[i] + n_samples],
                                    axis=1)

        for i in range(self.n_trials[1]):
            if i == 0:
                class_2 = self.eeg[:, self.pos_class_2[i] + n_cue:self.pos_class_2[i] + n_samples]
            else:
                class_2 = np.append(class_2, self.eeg[:, self.pos_class_2[i] + n_cue:self.pos_class_2[i] + n_samples],
                                    axis=1)
        return class_1, class_2

    def __bandpass(self):
        self.eeg[np.isnan(self.eeg)] = 0
        [b, a] = signal.butter(self.bp_order, np.divide(self.bp_frequency, self.sample_rate / 2), 'bandpass', False)
        self.eeg = signal.filtfilt(b, a, self.eeg, padtype='odd', padlen=3 * (max(len(b), len(a)) - 1), axis=1)

    def compute_csp(self, output_path):
        n_filters = 2  # defines how many virtual CSP channels are used

        # extract relevant epochs for each class
        data_1, data_2 = self.__extract_epochs()

        eigen_vectors = self.train_csp(data_1, data_2)

        # select csp filter
        selected_filter = np.ones(self.n_channels, dtype=bool)
        selected_filter[n_filters:len(selected_filter) - n_filters] = False
        self.csp_filter = eigen_vectors[:, selected_filter].T

        scipy.io.savemat(output_path + 'csp.mat', {'csp_filter': self.csp_filter})

    def compute_lda(self, output_path):
        # define extraction parameter --> Features need 1 second to rise + another
        # second due to the moving average filter --> 2sec delay!
        n_samples = int(np.floor(self.sample_rate * 3))
        csp_signal = np.square(np.matmul(self.csp_filter, self.eeg))

        window_length_seconds = 1
        window_length_samples = int(np.floor(window_length_seconds * self.sample_rate))
        csp_signal = signal.lfilter(np.ones(window_length_samples) / window_length_samples, 1, csp_signal)
        csp_signal = np.log10(csp_signal)

        x_train_1, x_train_2 = [], []
        for i in range(self.n_trials[0]):
            x_train_1.append(csp_signal[:, self.pos_class_1[i] + n_samples])

        for i in range(self.n_trials[1]):
            x_train_2.append(csp_signal[:, self.pos_class_2[i] + n_samples])

        x_train = np.append(np.array(x_train_1), np.array(x_train_2), axis=0)
        y_train = np.append(np.ones(self.n_trials[0], dtype=int), np.ones(self.n_trials[1], dtype=int) * 2)
        self.lda_coefficients = self.train_lda(x_train, y_train)

        scipy.io.savemat(output_path + 'lda.mat', {'W': self.lda_coefficients})

    @staticmethod
    def train_csp(data_1, data_2):
        cov_1 = np.cov(data_1)
        cov_2 = np.cov(data_2)
        norm_cov_1 = cov_1 / np.trace(cov_1)
        norm_cov_2 = cov_2 / np.trace(cov_2)

        # solve generalized eigenvalue problem and normalize
        eigen_values, eigen_vectors = scipy.linalg.eig(a=norm_cov_1, b=norm_cov_1 + norm_cov_2, left=True, right=False)
        eigen_vectors = eigen_vectors / np.max(np.abs(eigen_vectors), axis=0)

        # sort eigenvectors in descending order of the eigenvalues
        idx = eigen_values.argsort()[::-1]
        eigen_vectors = eigen_vectors[:, idx]
        return eigen_vectors

    @staticmethod
    def train_lda(data_train, classlabels, prior_prob=None):
        n, m = np.shape(data_train)
        classlabel = np.unique(classlabels)
        n_classes = len(classlabel)
        n_group = np.empty(n_classes)  # Group counts
        mean_group = np.empty((n_classes, m))  # Group sample means
        pooled_cov = np.zeros((m, m))  # Pooled covariance
        w = np.empty((n_classes, m + 1))  # model coefficients

        for i in range(n_classes):
            # Establish location and size of each class
            group = np.where(classlabels == classlabel[i])[0]
            n_group[i] = len(group)

            # Calculate group mean vectors
            mean_group[i] = np.mean(data_train[group, :], axis=0)

            # Accumulate pooled covariance information
            pooled_cov += ((n_group[i] - 1) / (n - n_classes)) * np.cov(data_train[group, :].T)

        if prior_prob is None:
            # Use the sample probabilities
            prior_prob = n_group / n

        # Loop over classes to calculate linear discriminant coefficients
        for i in range(n_classes):
            # Intermediate calculation for efficiency
            tmp = np.linalg.lstsq(pooled_cov.T, mean_group[i, :].T, rcond=None)[0].T

            # Constant
            w[i, 0] = -0.5 * np.matmul(tmp, mean_group[i, :]) + np.log(prior_prob[i])

            # Linear
            w[i, 1:np.shape(w)[1]] = tmp

        return w
