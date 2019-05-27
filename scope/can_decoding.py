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
    iteration = 0
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [0, 0, 0, 0, 0, 1]):
        del start_decoding_voltage_high[s+5+iteration]
        iteration += 1
    print start_decoding_voltage_high