#!/usr/bin/env python
# coding=utf-8
'''
Author: Liang Qing
Date:Wed 29 Mar 2017 05:35:15 PM HKT
Info:
'''
# switching frequency at the transmitter side (Hz)
base_frequency = 10000
# sampling frequency at the receiver side (Hz) 
sampling_frequency = 48000
# frame size (in raw bits)
frame_size = (12 + 32 + 8 + 4)
# total time slots for a frame
time_slots = 20
# 1 bit is represented by 'samples_per_bit' sample points
samples_per_bit = sampling_frequency / base_frequency
# frame length (in samples)
frame_length = samples_per_bit * frame_size

volt_threshold = 100

usb_card_index = 0
usb_volume = 5
usb_period_size = 480
usb_buffer_size = 9600 # buffer is filled every 200ms

thread_repeats = 10 # total buffer lasts 2s long

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

