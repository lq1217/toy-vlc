#!/usr/bin/env python
# coding=utf-8
'''
Author: Liang Qing
Date:Friday, March 17, 2017 AM11:46:20 HKT
Info:
'''
import sys
import time
import getopt

import numpy as np
import pylab as plt

from usb_soundcard  import *
from ook_manchester import *
from filters        import *
from vlc_config     import *

def fetch_raw_signal(fil):
    f = open(fil, 'r')
    raw = []
    for line in f:
        raw.extend(line.split())
    f.close()
    #inverse the signal phase, since the hardware induces a 180 phase shift 
    signal_raw = [-1 * int(x) for x in raw]
    return signal_raw

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    if not args:
        sys.exit(1)

    signal_raw = fetch_raw_signal(args[0])
    signal_filt_high = butter_highpass_filter(signal_raw, 100, sampling_frequency)
    signal_filt_median = list(median_filter(signal_filt_high, 3))
    
    bits = signal_binarize(signal_filt_median, volt_threshold)

    beacon_id, beacon_rssi, beacon_sigma, beacon_index = ook_decode(signal_filt_median, frame_length, samples_per_bit, volt_threshold) 

    id_array = np.asarray(beacon_id)
    rssi_array = np.asarray(beacon_rssi)
    id_index_sorted = np.argsort(id_array)
    id_sorted = np.sort(id_array)
    rssi_sorted = rssi_array[id_index_sorted]
    
    id_list = []
    rssi_list = []
    ind = 0
    while ind < len(id_array):
        id_item = id_sorted[ind]
        id_item_indices = np.where(id_sorted == id_item)[0]
        rssi_item = np.average(rssi_sorted[id_item_indices])
        id_list.append(id_item)
        rssi_list.append(rssi_item)

        ind += len(id_item_indices)

    print("ID:  %s"%id_list)
    print("RSSI:%s"%rssi_list)
    #for i in xrange(len(id_array)):
    #    print("[ID]:%d [RSSI]:%.3f" %(id_sorted[i], rssi_sorted[i]))
    #sigma_filt = list(signal.medfilt(beacon_sigma))
    #sigma_minus = list(np.asarray(beacon_sigma) - np.asarray(sigma_filt))
    #for i in xrange(len(beacon_id)):
    #    print("[ID]:%d [RSSI]:%.3f [SIGMA]:%.3f [INDEX]:%d" %(beacon_id[i], beacon_rssi[i], beacon_sigma[i], beacon_index[i]))
    
    time_chip = np.asarray(range(len(signal_filt_median)))/40.0 #time_interval = 1ms
    
    plt.ion()
    plt.figure(1)
    plt.plot(time_chip, list(np.asarray(signal_filt_median) / 32768.0), 'b')
    if beacon_id: 
        bits_amp = max(beacon_rssi) / float(32768) * 1.2
        plt.plot(time_chip, list(np.asarray(bits) * bits_amp), 'm--')
        plt.plot(time_chip[beacon_index], list(np.asarray(beacon_rssi) / 32768.0), 'g.-')
        plt.plot(time_chip[beacon_index], list(np.asarray(beacon_rssi) / 32768.0), 'r^')
        #plt.figure(2)
        #plt.plot(time_chip[beacon_index], list(np.asarray(beacon_sigma)), 'm.-')
        #plt.plot(time_chip[beacon_index], list(np.asarray(sigma_filt)), 'r.-')
        #plt.plot(time_chip[beacon_index], list(np.asarray(sigma_minus)), 'g.-')
        #plt.ylim([-1.2, 1.2])
    plt.show(block = True) 


