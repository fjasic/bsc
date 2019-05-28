from collections import Counter
import matplotlib.pyplot as plt
from kmp import KnuthMorrisPratt


def most_common(lst):
    return max(set(lst), key=lst.count)


def can_decoded(voltage_high, time, sample_interval):
    start_decoding_voltage_high = []
    for i in range(len(voltage_high) / sample_interval):
        if int(most_common(voltage_high[i * sample_interval:i * sample_interval + sample_interval])) == 0:
            start_decoding_voltage_high.append(1)
        else:
            start_decoding_voltage_high.append(0)
    for_deletion = []
    print start_decoding_voltage_high

    # bit stuffing removal
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [0, 0, 0, 0, 0, 1]):
        for_deletion.append(s)
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [1, 1, 1, 1, 1, 0]):
        for_deletion.append(s)
    iteration = 0
    while iteration < len(for_deletion):
        del start_decoding_voltage_high[for_deletion[iteration]+5-iteration]
        iteration += 1
    print "id: " + str(start_decoding_voltage_high[1:12])
    id_can = start_decoding_voltage_high[1:12]
    print "id(hex): " + "{0:0>2X}".format(int("".join(map(str, id_can)), 2))
    length_can = int("".join(map(str, start_decoding_voltage_high[16:20])), 2)
    print "length: " + str(length_can)
    data_can = start_decoding_voltage_high[20:20+4*length_can]
    print "data: " + str(data_can)
    crc_can = start_decoding_voltage_high[20+4*length_can:20+4*length_can+16]
    print "crc: " + str(crc_can)