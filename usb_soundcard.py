#!/usr/bin/env python
import os
import alsaaudio
import struct

class soundcard():
    def __init__(self, card_index, volume_gain, volume_agc, sample_rate, period_size, buffer_size):      
        self._card_index = card_index
        self._volume_gain = volume_gain
        self._volume_agc = volume_agc
        self._sample_rate = sample_rate
        self._period_size = period_size
        self._buffer_size = buffer_size    

    def set_card(self):
        if u'Device' in alsaaudio.cards():
            _card_index = alsaaudio.cards().index(u'Device')
        else:
            _card_index = 0
        if self._card_index != 0:
            _card_index = self._card_index
        
        os_flag = True
    
        if os.system("amixer -q -c %d sset 'Mic' %d" %(_card_index, self._volume_gain)):
            os_flag = False
        if os.system("amixer -q -c %d sset 'Auto Gain Control' %s" %(_card_index, self._volume_agc)):
            os_flag = False
        # Default attributes: Mono, 40000 Hz, 16 bit little endian samples
        inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, cardindex = _card_index)
        inp.setchannels(1)
        inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)    
        inp.setrate(self._sample_rate)
        inp.setperiodsize(self._period_size)
        self._inp = inp   
        
        return os_flag

    def capture_samples(self):
        samples = []
        valid_flag = True
        loops = self._buffer_size / self._period_size 
        while loops > 0:
            loops -= 1
            # Read 'period_size' samples from sound card
            l, data = self._inp.read()
            try:
                int_data=struct.unpack('%ih'%l, data)
            except:
                valid_flag = False
                break
            samples.extend(list(int_data))

        return valid_flag, samples
