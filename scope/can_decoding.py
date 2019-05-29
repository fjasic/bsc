# coding: utf-8
# -------------------------------------------------------------------------------
#  Decoding can signal and checking Cyclic redundancy check
#  TODO: lavinski uzastopni recesivni i dominanti biti
# -------------------------------------------------------------------------------

from collections import Counter
import matplotlib.pyplot as plt
from kmp import KnuthMorrisPratt


def most_common(lst):
    return max(set(lst), key=lst.count)


def can_decoded(voltage_high, time, sample_interval):
    start_decoding_voltage_high = []
    # reversing waveform
    for i in range(len(voltage_high) / sample_interval):
        if int(most_common(voltage_high[i * sample_interval:i 
                           * sample_interval + sample_interval])) == 0:
            start_decoding_voltage_high.append(1)
        else:
            start_decoding_voltage_high.append(0)
    for_deletion = []

    # bit stuffing removal
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [0, 0, 0, 0, 0, 1]):
        for_deletion.append(s)
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [1, 1, 1, 1, 1, 0]):
        for_deletion.append(s)
    iteration = 0
    while iteration < len(for_deletion):
        del start_decoding_voltage_high[for_deletion[iteration]+5-iteration]
        iteration += 1
    # print "id: " + str(start_decoding_voltage_high[1:12][::-1])
    id_can = start_decoding_voltage_high[1:12][::-1]
    print "id(hex): " + "{0:0>2X}".format(int("".join(map(str, id_can)), 2)),
    length_can = int("".join(map(str, start_decoding_voltage_high[16:20][::-1])), 2)
    print "||length: " + str(length_can),
    data_can = start_decoding_voltage_high[20:20+4*length_can][::-1]
    data_can_hex = []
    for i in range(length_can):
        data_can_hex.append("{0:0>2X}".format(
                int("".join(map(str, start_decoding_voltage_high[20+i*4:20+i*4+8])), 2)))
    print "||data: " + str(data_can_hex),
    crc_can = start_decoding_voltage_high[20+4*length_can:20+4*length_can+15][::-1]
    print "||crc: " + str(crc_can),
    for_crc = start_decoding_voltage_high[:20+4*length_can]
    crc = []
    result_crc = []
    for i in range(15):
        crc.append(0)
        result_crc.append(0)
    for i in range(len(for_crc)):
        doInvert = (for_crc[i] == "1") ^ crc[14]
        crc[14] = crc[13] ^ doInvert
        crc[13] = crc[12]
        crc[12] = crc[11]
        crc[11] = crc[10]
        crc[10] = crc[9] ^ doInvert
        crc[9] = crc[8]
        crc[8] = crc[7] ^ doInvert
        crc[7] = crc[6] ^ doInvert
        crc[6] = crc[5]
        crc[5] = crc[4]
        crc[4] = crc[3] ^ doInvert
        crc[3] = crc[2] ^ doInvert
        crc[2] = crc[1]
        crc[1] = crc[0]
        crc[0] = doInvert
    for i in range(15):
        if crc[i] == 1:
            result_crc[14-i] = 0
        else:
            result_crc[14-i] = 1
    
    if crc_can == result_crc:
        print "||crc is correct!"
    else:
        print "||crc is incorrect!"
    