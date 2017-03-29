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
    for eachline in f.readlines():
        line = eachline.split(' ')
        line.remove('\n')
        raw.extend(line)

    f.close()
    #inverse signal phase, since the hardware part induces a 180 phase difference
    signal_raw = [-1.0 * int(x) for x in raw]
    return signal_raw

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    if not args:
        sys.exit(1)

    signal_raw = fetch_raw_signal(args[0] + '.txt')
    signal_filt_high = butter_highpass_filter(signal_raw, 100, sampling_frequency)
    signal_filt_median = list(median_filter(signal_filt_high, 3))
    
    bits = signal_binarize(signal_filt_median, volt_threshold)

    beacon_id, beacon_rssi, beacon_sigma, beacon_index = ook_decode(signal_filt_median, frame_length, samples_per_bit, volt_threshold) 

    sigma_filt = list(signal.medfilt(beacon_sigma))
    sigma_minus = list(np.asarray(beacon_sigma) - np.asarray(sigma_filt))
    
    for i in xrange(len(beacon_id)):
        print("[ID]:%d [RSSI]:%.3f [SIGMA]:%.3f [INDEX]:%d" %(beacon_id[i], beacon_rssi[i], beacon_sigma[i], beacon_index[i]))
    
    time_chip = np.asarray(range(len(signal_filt_median)))#/40.0 #time_interval = 1ms
    try: 
        plt.figure(1)
        plt.plot(time_chip, list(np.asarray(signal_filt_median) / 32768.0), 'b')
        if beacon_id: 
            bits_amp = max(beacon_rssi) / float(32768) * 1.2
            plt.plot(time_chip, list(np.asarray(bits) * bits_amp), 'm--')
            plt.plot(time_chip[beacon_index], list(np.asarray(beacon_rssi) / 32768.0), 'g.-')
            plt.plot(time_chip[beacon_index], list(np.asarray(beacon_rssi) / 32768.0), 'r^')
            plt.figure(2)
            plt.plot(time_chip[beacon_index], list(np.asarray(beacon_sigma)), 'm.-')
            plt.plot(time_chip[beacon_index], list(np.asarray(sigma_filt)), 'r.-')
            plt.plot(time_chip[beacon_index], list(np.asarray(sigma_minus)), 'g.-')
        plt.ylim([-1.2, 1.2])
        plt.show() 
    except KeyboardInterrupt:
        exit(0)


