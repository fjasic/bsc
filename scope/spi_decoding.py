from collections import Counter
from kmp import KnuthMorrisPratt


def most_common(lst):
    return max(set(lst), key=lst.count)


def spi_decoded(voltage_clock, voltage_data, time, sample_interval):
    start_decoding_lin_data = []
    start_decoding_lin_clock = []
    for i in range(len(voltage_data) / sample_interval):
        start_decoding_lin_data.append(
            int(most_common(voltage_data[i * sample_interval:i * sample_interval + sample_interval])))
        start_decoding_lin_clock.append(
            int(most_common(voltage_clock[i * sample_interval:i * sample_interval + sample_interval])))
    br_flagova = 0
    data_final = []
    for s in KnuthMorrisPratt(start_decoding_lin_clock, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]):
        data_final.append("{0:0>2X}".format(
                int("".join(map(str, start_decoding_lin_data[s:s+16:2])), 2)))
    return data_final
