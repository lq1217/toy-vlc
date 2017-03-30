#!/usr/bin/env python
# coding=utf-8
'''
Author: Liang Qing
Date:Saturday, March 25, 2017 PM09:33:31 HKT
Info:
'''
def is_valid_bit(b):
    return (b == 1 or b == 0)

def _binarize(b, t):
    return (int(b - t > 0) - int(b + t < 0) + 1) * 0.5

#def signal_binarize(signal_raw, threshold):
#    return map(_binarize, signal_raw, [threshold] * len(signal_raw))
#def signal_binarize(signal_raw, threshold):
#    bits = [((int(b - threshold > 0) - int(b + threshold < 0) + 1) * 0.5) for b in signal_raw]
#
#    return bits

def signal_binarize(signal_raw, threshold):
    bits = []

    for i in signal_raw:
        if i > threshold:
            bits.append(1)
        elif i < -threshold:
            bits.append(0)
        else:
            bits.append(0.5)
    return bits  
    
def measure_bit_duration(bit_str, bit_len, bit_val, bit_ind):
    duration = 0
    idle_count = 0
    # only 1 or 0 is allowed for bit_val
    #if is_valid_bit(bit_val):
    # wait until the bit value flips
    while bit_ind < bit_len:
        if bit_str[bit_ind] != 1 - bit_val:
            # if an idle bit value (0.5) comes, increase idle_count by 1
            if bit_str[bit_ind] != bit_val:
                idle_count += 1
            # if >= 2 idle bits come, break    
            if idle_count > 1:   
                break
            #increase duation
            duration += 1
        else: 
            break
        bit_ind += 1

    return duration, (1 - bit_val), bit_ind

def measure_rssi(frame_buf, bit_ind_start, bit_ind_end):
    rssi = 0
    sigma = 0
    # calculate the average signal amplitude bounded by ind_start and ind_end
    _rssi = map(abs, frame_buf[bit_ind_start : bit_ind_end])
    rssi = sum(_rssi) / float(bit_ind_end - bit_ind_start)
    # calculate the corressponding standard deviation
    _sigma = [abs(each - rssi) for each in frame_buf[bit_ind_start : bit_ind_end]]
    sigma = sum(_sigma) / float(bit_ind_end - bit_ind_start)
    # normalize sigma to rssi average
    sigma /= rssi

    return rssi, sigma

def detect_sfr(bit_str, bit_len, bit_ind, bit_dur):
    sfr_flag = False
    
    ind_cur_bit = bit_ind
    ind_next_bit = bit_ind
    beacon_index = bit_len 

    while ind_cur_bit < bit_len:
        # wait until a '1' comes
        while ind_cur_bit < bit_len and bit_str[ind_cur_bit] != 1:
            ind_cur_bit += 1
        # calculate 1's duration, if > 3 times the theroretical bit duration, a SFR(start of frame) is identified
        duration, val_next_bit, ind_next_bit = measure_bit_duration(bit_str, bit_len, 1, ind_cur_bit)
        if duration > bit_dur * 3 and val_next_bit == 0:
            sfr_flag = True
            beacon_index = ind_next_bit    
            break

        ind_cur_bit = ind_next_bit

    return sfr_flag, beacon_index, ind_next_bit 

def sync_clock(bit_str, bit_len, bit_ind, bit_dur):
    sync_flag = False

    val_cur_bit = 0
    ind_cur_bit = bit_ind
    ind_next_bit = bit_ind

    clock_duration = 0
    clock_count = 0

    while ind_cur_bit < bit_len:
        # calculate the average bit duration of a '0101010' bit stream as the real bit duration 
        duration, val_next_bit, ind_next_bit = measure_bit_duration(bit_str, bit_len, val_cur_bit, ind_cur_bit)
        # if the bit duration we get deviates to much from the threoretical value, discard it
        if abs(duration - bit_dur) <= bit_dur / 2:
            clock_duration += duration
            clock_count += 1
        else:
            break

        if clock_count >= 7:
            if val_next_bit == 1:
                clock_duration /= 7.0
                sync_flag = True
            break

        val_cur_bit = val_next_bit
        ind_cur_bit = ind_next_bit

    return sync_flag, clock_duration, ind_next_bit

def decode_frame(frame_buf, bit_len, bit_ind, bit_dur, threshold):
    # binarize the analog sigmal with a given threshold
    bit_str = signal_binarize(frame_buf, threshold)
    # contain recovered bit stream with manchester coding
    bits_with_manchester = []
    # contain recovered bit stream without manchester coding
    bits_without_manchester = []
    
    val_next_bit = 0

    rssi_ind_start = 0
    rssi_ind_end = 1
    
    beacon_id = 0
    beacon_rssi = 0
    beacon_rssi_sigma = 0

    sfr_flag = False
    sync_flag = False
    decode_flag = False
    check_flag = False

    sfr_flag, beacon_index, ind_next_bit = detect_sfr(bit_str, bit_len, bit_ind, bit_dur)

    if sfr_flag:
        # record the left boundary where rssi begins to calculate 
        rssi_ind_start = ind_next_bit
       
        ind_cur_bit = ind_next_bit
        
        sync_flag, clock_duration, ind_next_bit = sync_clock(bit_str, bit_len, ind_cur_bit, bit_dur)
        
        if sync_flag:            
            val_cur_bit = 1
            ind_cur_bit = ind_next_bit
            # update the bit duration using the clock_duration measured in clock syncronization
            # if abs(clock_duration - bit_dur) < 0.5:
            bit_dur = clock_duration  
            #print bit_dur    
            while ind_cur_bit < bit_len:
                duration, val_next_bit, ind_next_bit = measure_bit_duration(bit_str, bit_len, val_cur_bit, ind_cur_bit)
                # a single '1' or '0' detected
                if duration >= bit_dur * 0.5 and duration < bit_dur * 1.5:
                    bits_with_manchester.append(int(val_cur_bit))
                # a pair of '1's or '0's are detected
                elif duration >= bit_dur * 1.5 and duration < bit_dur * 2.5:
                    bits_with_manchester.append(int(val_cur_bit))
                    bits_with_manchester.append(int(val_cur_bit))
                # EFR(end of frame) is detected   
                elif duration > bit_dur * 2.5:
                    buf_len = len(bits_with_manchester)
                    # only if the buf_len equals 40 or 41 does the decoding result seems to be correct
                    if buf_len == 40 or buf_len == 41:
                        # if buf_len = 40, append a '0' to the end of bits buffer
                        if buf_len == 40:
                            bits_with_manchester.append(int(0))
                        # discard the first element in bits buffer, which is indeed a '1'-bit of the preamble    
                        bits_with_manchester.pop(0)
                        # record the right boundary where rssi ends to calculate 
                        rssi_ind_end = ind_next_bit
                        beacon_rssi, beacon_rssi_sigma = measure_rssi(frame_buf, rssi_ind_start, rssi_ind_end)
                        #print beacon_rssi, beacon_rssi_sigma
                        decode_flag = True
                    break
                else:
                    # no more beacons can be detected, break
                    break

                val_cur_bit = val_next_bit
                ind_cur_bit = ind_next_bit

            if decode_flag:
                # translate 2 bits encoded in manchester coding into 1 bit
                i = 0
                while i + 1 < 40:
                    bits_without_manchester.append(int(bits_with_manchester[i] < bits_with_manchester[i + 1]))
                    i += 2
                # recover beacon id (16 bits = 2 Bytes)
                beacon_id = 0
                i = 0
                while i < 16:
                    beacon_id |= (bits_without_manchester[i] << (15 - i))
                    i += 1   
                # recover the checksum (4 bits = a half Byte)
                check_sum = 0
                while i < 20:
                    check_sum |= (bits_without_manchester[i] << (19 - i))
                    i += 1
                # check whether the received checksum matchs the calculated one, If yes, give the check_flag a True
                if check_sum == cal_check_sum(beacon_id):
                    check_flag = True
    
    return check_flag, decode_flag, sync_flag, sfr_flag, beacon_id, beacon_rssi, beacon_rssi_sigma, beacon_index, ind_next_bit, val_next_bit           

def cal_check_sum(x):
    i = 0
    check = 0
    while i < 4:
        check ^= (x & 0x000f)
        x >>= 4
        i += 1

    return check   

def ook_decode(decoding_buffer, frame_length, bit_duration, threshold = 100):
    buffer_length = len(decoding_buffer)
    
    signal_padding = []
    # beacon id (0-65536)
    beacon_id_list = []
    # beacon rssi (average)
    beacon_rssi_list = []
    # standard deviation of beacon rssi
    beacon_rssi_sigma_list = []
    # index of detected beacons within the selected decoding buffer 
    beacon_index_list = []
    # decoding operates in a sliding fashion, advance this size each time
    buffer_sliding_size = frame_length * 10

    lucky_count = 0
    lucky_index = 0
    
    buffer_offset = 0

    while buffer_offset < buffer_length:
        if buffer_offset + buffer_sliding_size < buffer_length:
            signal_clip = signal_padding + (decoding_buffer[buffer_offset : buffer_offset + buffer_sliding_size])
        else:
            signal_clip = signal_padding + (decoding_buffer[buffer_offset : ])

        clip_length = len(signal_clip)

        ind_cur_bit = 0
        
        while ind_cur_bit < clip_length:
            check_flag, decode_flag, sync_flag, sfr_flag, beacon_id, beacon_rssi, beacon_rssi_sigma, beacon_index, ind_next_bit, val_next_bit  \
                    = decode_frame(signal_clip, clip_length, ind_cur_bit, bit_duration, threshold)
            #print check_flag, decode_flag, sync_flag, sfr_flag, beacon_id, beacon_rssi, beacon_index + buffer_offset - len(signal_padding)
            # if check_flag is set True, a reliable beacon is detected, save it 
            if check_flag:
                _beacon_index = beacon_index + buffer_offset - len(signal_padding)
                # check whether the detected beacon is already in the list
                if _beacon_index in beacon_index_list:
                    pass
                else:
                    beacon_id_list.append(beacon_id)
                    beacon_rssi_list.append(beacon_rssi)
                    beacon_rssi_sigma_list.append(beacon_rssi_sigma)
                    beacon_index_list.append(_beacon_index)
                    
                    lucky_count += 1
                    # get the lucky index
                    lucky_index = ind_next_bit - frame_length / 2 
                    #print 'Find %d beacons successfully !' %lucky_count
            # if a sfr could not be detected, it's time to terminate this round    
            elif not sfr_flag:
                break

            ind_cur_bit = ind_next_bit
        # maybe some data at the end of 'signal_clip' is still usefull in the next round, save it into signal_padding
        if not check_flag and not decode_flag and sync_flag:
            signal_padding = signal_clip[lucky_index : ]
        else:
            signal_padding = signal_clip[ind_next_bit : ]
        # advance some steps
        buffer_offset += buffer_sliding_size
    # if we get some beacons, do a double check before the cheer whether the beacon signal is corrupted by others. 
    # if so, discard it since it does no good to localization. usually, the signal amplitude will fluctuate severely under corruption
    if beacon_id_list:
        average_rssi_sigma = sum(beacon_rssi_sigma_list) / len(beacon_rssi_sigma_list)
        #print average_rssi_sigma
        for (i, s) in enumerate(beacon_rssi_sigma_list):
            if s - average_rssi_sigma > 0.05:
                _id = beacon_id_list.pop(i)
                _rssi = beacon_rssi_list.pop(i)
                _sigma = beacon_rssi_sigma_list.pop(i)
                _ind = beacon_index_list.pop(i)    
                #print "Beacon: ID=%d, rssi=%.3f, sigma=%.3f, index=%d is removed !" %(_id, _rssi, _sigma, _ind)

    return beacon_id_list, beacon_rssi_list, beacon_rssi_sigma_list, beacon_index_list

