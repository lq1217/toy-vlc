#!/usr/bin/env python

import os
import sys
import time
import getopt

import numpy as np
import pylab as plt

import alsaaudio
import struct

def usage():
    print('usage: record.py [-d <device_id>] <file>')
    sys.exit(2)

if __name__ == '__main__':
    
    card_list = alsaaudio.cards()
    print card_list

    if u'Device' in card_list:
        device_index = card_list.index(u'Device')
    else:
        device_index = 0
    
    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    for o, a in opts:
        if o == '-d':
            device_index = int(a)
    if not args:
        usage()

    volume = 16
    
    os.system("amixer -q -c %d sset 'Mic' %d" %(device_index, volume))

    f = open(args[0]+'.txt', 'w')

    # Open the device in nonblocking capture mode. The last argument could
    # just as well have been zero for blocking mode. Then we could have
    # left out the sleep call in the bottom of the loop
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, cardindex = device_index)

    # Set attributes: Mono, 44100 Hz, 16 bit little endian samples
    inp.setchannels(1)
    inp.setrate(48000)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

    # The period size controls the internal number of frames per period.
    # The significance of this parameter is documented in the ALSA api.
    # For our purposes, it is suficcient to know that reads from the device
    # will return this many frames. Each frame being 2 bytes long.
    # This means that the reads below will return either 320 bytes of data
    # or 0 bytes of data. The latter is possible because we are in nonblocking
    # mode.
    inp.setperiodsize(480)

    print("record 2s later")
    time.sleep(2) # delay 2 seconds
    
    data_cat = []
    loops = 500
    while loops > 0:
        loops -= 1
        # Read data from device
        l, data = inp.read()
        try:
            int_data=struct.unpack('%ih'%l, data)
        except:
            print 'error, check'
            exit(1)
        for a in int_data:
            f.write("%d "%a)
        f.write('\n')   
        data_cat.extend(list(int_data))
    f.close()
    
    os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (0.5, 2500))
   
    try:
        plt.figure(1)
        plt.plot(data_cat)
        plt.show()
    except KeyboardInterrupt:
        exit(0)
