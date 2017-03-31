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
    fil_lst = []
    try:
        fil_lst = next(os.walk(args[0]))[2]
    except:
        print bcolors.WARNING + 'Can not find files' + bcolors.ENDC

    txt_lst = [x for x in fil_lst if len(x) == 6 and x[-4 : ] == '.txt']

    #print txt_lst

    finger_prints_samples = np.zeros((36, 4))

    for fil in txt_lst:
        signal_raw = fetch_raw_signal(args[0] + fil)
        signal_filt_high = butter_highpass_filter(signal_raw, 100, sampling_frequency)
        signal_filt_median = list(median_filter(signal_filt_high, 3))
        
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
        
        if id_list == [11, 12, 13, 14]:
            pass
        else:
            for ind, _id in enumerate([11, 12, 13, 14]):
                if _id not in id_list:
                    id_list.insert(ind, _id)
                    rssi_list.insert(ind, 0)
        print("FILE:%s"%fil)
        print("ID:  %s"%id_list)
        print("RSSI:%s"%rssi_list)

        _map_x = int(fil[1])
        _map_y = int(fil[0])
        if _map_x >=0 and _map_x <=5 and _map_y >=0 and _map_y <= 5:
            finger_prints_samples[_map_y * 6 + _map_x] = np.asarray(rssi_list)
        else:
            print bcolors.FAIL+ 'Illegal Coordinates [0, 0] to [5, 5]' + bcolors.ENDC
    print 'fingerprints map samples (4 by 6 by 6)'
    print finger_prints_samples

    np.savetxt('finger_prints.map', finger_prints_samples, fmt = '%.3f')
    
