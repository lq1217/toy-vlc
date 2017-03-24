#!/usr/bin/env python
# coding=utf-8
'''
Author: Liang Qing
Date:Friday, March 17, 2017 AM11:46:20 HKT
Info:
'''

#from __future__ import division

import sys
import getopt
import pylab as pl
import numpy as np
import copy
from scipy import signal

# switching frequency at the transmitter side (Hz)
base_frequency = 10000
# sampling frequency at the receiver side (Hz) 
sampling_frequency = 40000
# size of pn sequence (in raw bits)
pnseq_size = 31
# message size (in message bits)
mesg_size = 5
# total time slots for a frame
time_slots = 20

# 1 bit is represented by 'samples_per_bit' sample points
samples_per_bit = sampling_frequency / base_frequency
# pnseq length (in samples)
pnseq_length = samples_per_bit * pnseq_size
# message length (in samples)
mesg_length = pnseq_length * mesg_size 
# frame length (in samples)
frame_length = mesg_length * time_slots



def get_raws(fname):
    f = open(fname, 'r')

    content = []
    for line in f:
        content = line.split(',')
    content.remove('')

    f.close()

    #inverse the phase of raw signal, as the hardware induces a 180 phase difference
    #transform s16 integer into float [-1, 1]
    raws = [int(v)/-32768.0 for v in content]
    #print raws    
    return raws

def generate_refcodes(samples_per_bit):
    f = open('code.txt', 'r')

    codebook = []
    for line in f:
        codebook.append([int(x) for x in line.split()])

    f.close()

    bi_codebook = [] 
    for each in codebook:
        temp = []
        for x in each:
            if x == 0:
                x = -1
            temp.append(x)
        bi_codebook.append(temp)
    #print bi_codebook
    #for i in bi_codebook:
    #    print sum(i) 

    code_ref = []
    for code in bi_codebook:
        code_extend = [None] * pnseq_length
        for i in range(samples_per_bit):
            code_extend[i::samples_per_bit] = code
       
        code_ref.append(code_extend)

    return code_ref  

def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

def sliding_xcorr(raw_sig, pn_seq):
    sig_len = len(raw_sig)
    pn_len = len(pn_seq)
    res = []
    
    i = 0
    while (i + pn_len) <= sig_len:
        res.append(np.inner(raw_sig[i : (i + pn_len)], pn_seq))
        i += 1

    res_ = np.asarray(res) / np.inner(pn_seq, pn_seq)

    #res_filt = butter_lowpass_filter(res_, 1000, sampling_frequency)

    return list(res_)

def find_max_res(res, code_len, res_thresh):
    res_len = len(res)

    max_res_ind = []
    max_res_val = []

    cursor = 0
   
    while cursor < res_len:
        if cursor + code_len < res_len:
            res_chip = res[cursor : (cursor + code_len)]
        else:
            res_chip = res[cursor : ]
        
        max_val = max(res_chip)
        min_val = min(res_chip)

        max_ind = res_chip.index(max_val) + cursor
        min_ind = res_chip.index(min_val) + cursor
        
        max_flag = False
        min_flag = False
       
        if max_ind not in max_res_ind:
            if max_val > res_thresh:
                max_res_ind.append(max_ind)
                max_res_val.append(max_val)
                max_flag = True
        if min_ind not in max_res_ind:
            if min_val < -res_thresh:
                max_res_ind.append(min_ind)
                max_res_val.append(min_val)
                min_flag = True

        if max_flag == True and min_flag == True:
            if max_ind > min_ind:
                i, j = max_res_ind.index(max_ind), max_res_ind.index(min_ind)
                max_res_ind[i], max_res_ind[j] = max_res_ind[j], max_res_ind[i]
                max_res_val[i], max_res_val[j] = max_res_val[j], max_res_val[i]
       
        cursor += code_len / 2  
    
    return max_res_ind, max_res_val

def process_frame(frame, code_ref, ind0, coef):
    frame_len = len(frame)
    code_len = len(code_ref[0])
    res_thresh = average_energy(frame) * coef

    res_his = []
    res_ind = []
    res_val = []
    
    for refcode in code_ref:
        res = sliding_xcorr(frame, refcode)
        ind, val = find_max_res(res, code_len, res_thresh)
        
        ind = list(np.asarray(ind) + ind0)
        res_his.append(res)
        res_ind.append(ind)
        res_val.append(val)
    
    return res_his, res_ind, res_val

def decode(signal_buf, frame_len, code_ref):
    buf_len = len(signal_buf)
    code_len = len(code_ref[0])
    code_num = len(code_ref)

    cursor = 0

    res_his_buf = []
    res_ind_buf = []
    res_val_buf = []
    
    _count = 0
    while _count < code_num:
        res_his_buf.append([])
        res_ind_buf.append([])
        res_val_buf.append([])

        _count += 1

    while cursor + frame_len < buf_len:
        frame_chip = signal_buf[cursor : (cursor + frame_len)]
        res_his, res_ind, res_val = process_frame(frame_chip, code_ref, cursor, 0.6)
       
        for _count in range(code_num):
            res_his_buf[_count].extend(res_his[_count])
            res_ind_buf[_count].extend(res_ind[_count])
            res_val_buf[_count].extend(res_val[_count])

        cursor = cursor + frame_len - (code_len - 1)

    return res_his_buf, res_ind_buf, res_val_buf



    #signal_reconstruct = [0] * len(raw_frame)

    #for i in res_ind:
    #    signal_reconstruct[i : i+pnseq_length] = list(np.asarray(code_ref[code]) * max_avg_res)

    #res_sig.append(signal_reconstruct)
    #res_code.append(code)
    #res_comp.append(max_avg_res)

    #sig_his.append(raw_frame)
    #raw_frame = list(np.asarray(raw_frame) - np.asarray(signal_reconstruct))

   
    #return res_sig, res_code, res_comp, sig_his

def average_energy(sig):
    tmp = 0
    for i in sig:
        tmp += abs(i)
    return float(tmp)/len(sig)  

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

def usage():
    sys.exit(2)

if __name__ == '__main__':

    opts, args = getopt.getopt(sys.argv[1:], 'd:')
    if not args:
        usage()

    fname = args[0] + '.txt'

    #raw_signal = get_raws('./data/1bulb/55.txt')
    #raw_signal = get_raws('./data/2bulbs/21.txt')
    raw_signal = get_raws(fname)
    #signal_filt_high = butter_highpass_filter(raw_signal, 1000, sampling_frequency)
    #signal_filt_low = butter_lowpass_filter(signal_filt_high, 15000, sampling_frequency)
    #apply a median filter to raw signal
    #signal_filt = signal.medfilt(signal_filt_low, 5)
    #signal_filt = raw_signal

    #calculate the mean signal
    #pad with (pnseq_length - 1) 0s ahead of filted signal
    win_len = sampling_frequency / 100 * 1
    sig_padding = np.asarray([0] * (win_len - 1) + list(raw_signal))
    signal_mean = running_mean(sig_padding, win_len)

    #remove the mean signal from the filted signal
    #signal_use = list(np.asarray(raw_signal) - np.asarray(signal_mean))
    signal_use = list(raw_signal)
    signal_chip = signal_use[:(frame_length * 2)]
    code_ref = generate_refcodes(samples_per_bit)

    #res_his, res_ind, res_val = decode(signal_chip, frame_length, code_ref)
    #print res_ind[0], res_ind[1], res_ind[2], res_ind[4] 
    
    #try:
    #    for key in max_res.keys():
    #        signal_reconstruct[key:key+pnseq_length] = list(np.asarray(code_ref[1]) * max_res[key])
    #except:
    #    print 'Cannot recover this componemt'
    ##print signal_reconstruct
    ##print response[key-10:key+10]

    #res_sig, res_code, res_comp, sig_his = decode_frame(signal_chip, code_ref)
    #print res_code
    #print res_comp
    #sig_reduced = medfilt(sig_his[1])
    
    time_chip = np.asarray(range(len(signal_chip)))#/4000.0 #time_interval = 0.1s
    
    pl.ion()
    pl.figure(1)
    #pl.plot(signal_filt_low)
    #pl.plot(raw_signal)
    #pl.plot(response1)
    pl.plot(signal_chip)
    #pl.plot(res_his[0])
    #pl.plot(res_ind[0], res_val[0], 'r^')
    pl.show() 
    #pl.figure(2)
    #cnt = 0;
    #for res in res_his:
    #    cnt += 1
    #    if cnt > 3:
    #        break
    #    pl.subplot(2, 2, cnt)
    #    handle = pl.plot(time_chip[:len(res)], list(abs(np.asarray(res))))
    #    if len(res_ind):
    #        pl.plot(res_ind[cnt - 1], res_val[cnt - 1], 'r^')
    #    pl.legend(handle, str(cnt))

    #    energy_threshold = average_energy(signal_chip) * 0.6
    #    pl.plot(time_chip[:len(res)], [energy_threshold] * len(res))
    #    pl.plot(time_chip[:len(res)], [-energy_threshold] * len(res))
    #pl.subplot(2, 2, cnt)
    #res = res_his[4]
    #handle = pl.plot(time_chip[:len(res)], res)
    #pl.legend(handle, str(cnt))
    #pl.plot(time_chip[:len(res)], [energy_threshold] * len(res))
    #pl.plot(time_chip[:len(res)], [-energy_threshold] * len(res))
    pl.show()

    try:
        input('wait..')
    except:
        exit(0)


