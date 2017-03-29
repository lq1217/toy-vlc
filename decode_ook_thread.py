#!/usr/bin/env python
import os
import sys
import time
import getopt

import numpy as np
import pylab as plt
import threading
#from threading import Thread

from usb_soundcard  import *
from ook_manchester import *
from filters        import *
from vlc_config     import *

class soundcard_thread(threading.Thread):
    def __init__(self, times, card_index, volume_gain, volume_agc, sample_rate, period_size, buffer_size):
        threading.Thread.__init__(self)
        self._times = times
        self._mysoundcard = soundcard(card_index, volume_gain, volume_agc, sample_rate, period_size, buffer_size)
        self._ready = self._mysoundcard.set_card()

    def run(self):
        global first_buffer, second_buffer, first_ready_flag, second_ready_flag, valid_flag, first_mutex, second_mutex
        
        print bcolors.OKBLUE + 'soundcard thread is running' + bcolors.ENDC

        _count = 0
        while _count < self._times:
            if not first_ready_flag:    
                first_mutex.acquire()

                valid_flag, first_buffer = self._mysoundcard.capture_samples()
                first_ready_flag = True

                first_mutex.release()

                _count += 1
            elif not second_ready_flag:
                second_mutex.acquire()

                valid_flag, second_buffer = self._mysoundcard.capture_samples()
                second_ready_flag = True

                second_mutex.release()

                _count += 1
            else:
                pass

        print bcolors.OKBLUE + 'soundcard thread exited successfully' + bcolors.ENDC
            
class decoding_thread(threading.Thread):
    def __init__(self, times, fil_raw, fil_res, sampling_frequency, samples_per_bit, frame_length, threshold):
        threading.Thread.__init__(self)
        self._fil_raw = fil_raw
        self._fil_res = fil_res
        self._times = times

        self._sampling_frequency = sampling_frequency
        self._samples_per_bit = samples_per_bit
        self._frame_length = frame_length
        self._threshold = threshold
    
    def run(self):
        global first_buffer, second_buffer, first_ready_flag, second_ready_flag, valid_flag, first_mutex, second_mutex
        
        f_res = open(self._fil_res, 'w')
        f_raw = open(self._fil_raw, 'w')
        f_res.close()
        f_raw.close()

        print bcolors.OKGREEN + 'decoding thread is running' + bcolors.ENDC

        _count = 0

        while _count < self._times:
            if first_ready_flag:
                first_mutex.acquire()

                print 'decoding first buffer'
                
                card_buffer = list(np.asarray(first_buffer) * -1.0)

                if valid_flag:
                    start_time = time.time()
                    
                    f_res = open(self._fil_res, 'a')
                    f_raw = open(self._fil_raw, 'a')
                    
                    sig_filt_high = butter_highpass_filter(card_buffer, 100, self._sampling_frequency)
                    signal_filt = list(median_filter(sig_filt_high, 3))
                    
                    beacon_id, beacon_rssi, beacon_sigma, beacon_index \
                        = ook_decode(signal_filt, self._frame_length, self._samples_per_bit, self._threshold) 

                    for i in xrange(len(beacon_id)):
                        f_res.write("%d %.3f %.3f %d\n" %(beacon_id[i], beacon_rssi[i], beacon_sigma[i], beacon_index[i]))
                    
                    for x in first_buffer:
                        f_raw.write('%d '%x)
                        f_raw.write('\n')
                    
                    f_res.close()
                    f_raw.close()   
        
                    print("--- %s seconds ---" % (time.time() - start_time))
                else:
                    print bcolors.FAIL + 'soundcard reading error !' + bcolors.ENDC
                first_ready_flag = False

                first_mutex.release()

                _count += 1
            elif second_ready_flag:
                second_mutex.acquire()

                print 'decoding second buffer' 
                
                card_buffer = list(np.asarray(second_buffer) * -1.0)

                if valid_flag:
                    start_time = time.time()
                    
                    f_res = open(self._fil_res, 'a')
                    f_raw = open(self._fil_raw, 'a')
                    
                    sig_filt_high = butter_highpass_filter(card_buffer, 100, self._sampling_frequency)
                    signal_filt = list(median_filter(sig_filt_high, 3))
                    
                    beacon_id, beacon_rssi, beacon_sigma, beacon_index \
                        = ook_decode(signal_filt, self._frame_length, self._samples_per_bit, self._threshold) 
                    if beacon_id:
                        for i in xrange(len(beacon_id)):
                            f_res.write("%d %.3f %.3f %d\n" %(beacon_id[i], beacon_rssi[i], beacon_sigma[i], beacon_index[i]))
                    
                    for x in second_buffer:
                        f_raw.write('%d '%x)
                        f_raw.write('\n')
                    
                    f_res.close()
                    f_raw.close()   
        
                    print("--- %s seconds ---" % (time.time() - start_time))
                else:
                    print bcolors.FAIL + 'soundcard reading error !' + bcolors.ENDC

                second_ready_flag = False

                second_mutex.release()

                _count += 1
            else:
                pass
        print bcolors.OKGREEN + 'decodeing thread exited successfully' + bcolors.ENDC


def usage():
    print "usage: ./*.py <position> [00-55]"
    exit(1)

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    if not args: 
        usage()
    file_raw = 'raw' + args[0] + '.txt'
    file_res = 'res' + args[0] + '.txt'

    _counts = thread_repeats

    global first_buffer, second_buffer, first_ready_flag, valid_flag, second_ready_flag, first_mutex, second_mutex
    
    first_mutex = threading.Lock()
    second_mutex = threading.Lock()

    first_ready_flag = False
    second_ready_flag = False

    soundcardThread = soundcard_thread(_counts, usb_card_index, usb_volume, 'off', sampling_frequency, usb_period_size, usb_buffer_size)
    if not soundcardThread._ready:
        print bcolors.WARNING + "soundcard failed to configure " + bcolors.ENDC
        exit(1)
    else:
        print bcolors.OKGREEN + "soundcard configured successfully" + bcolors.ENDC
    
    decodingThread = decoding_thread(_counts, file_raw, file_res, sampling_frequency, samples_per_bit, frame_length, volt_threshold)

    soundcardThread.start()
    decodingThread.start()

    soundcardThread.join()
    decodingThread.join()

    print bcolors.BOLD + 'END' + bcolors.ENDC
