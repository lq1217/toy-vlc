#!/usr/bin/env python
# coding=utf-8
'''
Author: Liang Qing
Date:Monday, March 27, 2017 PM08:25:18 HKT
Info:
'''
import sys
import getopt
import numpy as np
import pylab as plt

def fetch_raw_signal(fil):
    f = open(fil, 'r')
    raw = []
    for line in f:
        raw.extend(line.split())
    f.close()
    #inverse the signal phase, since the hardware induces a 180 phase shift 
    signal_raw = [-1 * int(x) for x in raw]
    return signal_raw

def usage():
    print "usage: ./display.py <file>"
    exit(1)

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    if not args:
        usage()

    signal = fetch_raw_signal(args[0])
   
    plt.ion()
    plt.plot(signal)
    plt.show(block = True)
    
