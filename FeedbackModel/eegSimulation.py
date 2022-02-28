import json
import numpy as np
import os
import pytiaclient
from pylsl import StreamInfo, StreamOutlet, local_clock
import subprocess
import time

import bci_modules

data = []


def receive_data_from_tia():
    client.start_data()
    global data
    while True:
        data = client.get_data_chunk(blocking=True)[0]


# start TiA server
subprocess.run(["1a_start_signalserver_eegsim.bat"])

# info about TiA server
TCP_IP = "127.0.0.1"
TCP_PORT = 9000

# connect to TiA server
client = pytiaclient.TIAClient()
client.connect(TCP_IP, TCP_PORT)
meta_info = client._metainfo

# get info about the signal
s_rate = int(meta_info["signals"][0]["samplingRate"])
n_channels = int(meta_info["signals"][0]["numChannels"])
block_size = int(meta_info["signals"][0]["blockSize"])

# create a LSL stream and a outlet
cwd = os.getcwd()
config_file = cwd + '/../bci-config.json'
with open(config_file) as json_file:
    config = json.load(json_file)

eeg_stream_stgs = config['general-settings']['lsl-streams']['eeg']
info = StreamInfo(name=eeg_stream_stgs['name'], channel_count=n_channels, nominal_srate=s_rate,
                  channel_format='float32', source_id=eeg_stream_stgs['id'])
outlet = StreamOutlet(info)

# start data transmission
bci_modules.threading.Thread(target=receive_data_from_tia).start()

# send data via LSL
start_time = local_clock()
sent_samples = 0
pos = 0
max_samples = 100000

while True:
    if not data:
        time.sleep(0.01)
        continue
    else:
        elapsed_time = local_clock() - start_time
        required_samples = int(s_rate * elapsed_time) - sent_samples
        for sample_ix in range(required_samples):
            my_sample = np.array(data)[:, pos]
            outlet.push_sample(my_sample)

            if pos < block_size - 1:
                pos += 1
            else:
                pos = 0

        sent_samples += required_samples
        if sent_samples > max_samples:
            sent_samples = 0
            start_time = local_clock()
        time.sleep(0.01)

client.stop_data()
client.close()
