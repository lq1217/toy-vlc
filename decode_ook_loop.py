#!/usr/bin/env python

import sys
import time
import getopt

import numpy as np
import pylab as plt

from usb_soundcard  import *
from ook_manchester import *
from filters        import *
from vlc_config     import *

def usage():
    print "usage: ./decode_real_time_v1.py [file prefix] [repeating times]"
    exit(1)

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    if not args:
        usage()
    else:
        try:
            _counts = int(args[1])
        except:
            _counts = 5

    mysoundcard = soundcard(usb_card_index, usb_volume, 'off', sampling_frequency, usb_period_size, usb_buffer_size)
    if not mysoundcard.set_card():
        print bcolors.WARNING + "soundcard failed to configure " + bcolors.ENDC
        exit(1)
    else:
        print bcolors.OKGREEN + "soundcard configured successfully" + bcolors.ENDC

    f_res = open(args[0] + 'res.txt', 'w')
    f_raw = open(args[0] + 'raw.txt', 'w')
    f_res.close()
    f_raw.close()

    counter = 0
    while counter < _counts:
        counter += 1

        start_time = time.time()
        
        valid_flag, card_buffer = mysoundcard.capture_samples()
        
        print("--- %s seconds ---" % (time.time() - start_time))
        
        _card_buffer = list(np.asarray(card_buffer) * -1.0)
        
        if valid_flag:
            start_time = time.time()
            
            f_res = open(args[0] + 'res.txt', 'a')
            f_raw = open(args[0] + 'raw.txt', 'a')
            
            sig_filt_high = butter_highpass_filter(_card_buffer, 100, sampling_frequency)
            signal_filt = list(median_filter(sig_filt_high, 3))
            
            beacon_id, beacon_rssi, beacon_sigma, beacon_index \
                = ook_decode(signal_filt, frame_length, samples_per_bit, volt_threshold) 
            if beacon_id:
                for i in xrange(len(beacon_id)):
                    f_res.write("%d %.3f %.3f %d\n" %(beacon_id[i], beacon_rssi[i], beacon_sigma[i], beacon_index[i]))
            
            for x in card_buffer:
                f_raw.write('%d '%x)
                f_raw.write('\n')
            
            f_res.close()
            f_raw.close()   
    
            print("--- %s seconds ---" % (time.time() - start_time))
        else:
            print bcolors.FAIL + 'soundcard reading error !' + bcolors.ENDC
    print bcolors.BOLD + 'END' + bcolors.ENDC
