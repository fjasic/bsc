# coding: utf-8
"""
Decodes I2C signal and returns decoded data.
Used modules in i2c_decoding.py :
--matplotlib                         2.2.4
--collections
--kmp from my script KnuthMorrisPratt(kmp.py)
--colorama                           0.4.1
"""
from collections import Counter
from kmp import KnuthMorrisPratt
from collections import OrderedDict
import matplotlib.pyplot as plt


def most_common(lst):
    """
    Return the most common element from list.
    -----------------------------------------
    @param lst -- List from which most common element is found.
    -----------------------------------------
    """
    return max(set(lst), key=lst.count)


def i2c_decoded(sda_to_decode, scl_to_decode, sample_period):
    """
    Decodes I2C signal.
    -------------------
    @param sda_to_decode -- SDA data from oscilloscope which we need to process.(data for I2C)
    @param scl_to_decode -- SCL data from oscilloscope which we need to process.(clock for I2C)
    @param sample_period -- Sample rate of oscilloscope.
    -------------------
    """
    start_decoding_i2c_data = []
    start_decoding_i2c_clock = []
    for i in range(len(sda_to_decode) / sample_period):
        start_decoding_i2c_data.append(
            int(most_common(sda_to_decode[i * sample_period:i * sample_period + sample_period])))
        start_decoding_i2c_clock.append(
            int(most_common(scl_to_decode[i * sample_period:i * sample_period + sample_period])))
    print start_decoding_i2c_data
    plt.show()
    data_final = []
    match_sda = []
    match_scl = []
    match = []
    for s in KnuthMorrisPratt(start_decoding_i2c_data, [1, 1, 1, 1, 1, 1]):
        match_sda.append(s)
    for s in KnuthMorrisPratt(start_decoding_i2c_clock, [1, 1, 1, 1, 1, 1, 1, 1]):
        match_scl.append(s)
    mapping = OrderedDict()
    for x in match_scl:
        mapping[x] = x if x in match_sda else 'Missing'

    for x in match_sda:
        mapping[x] = x if x in match_scl else 'Missing'

    # table_format = '{:<10} {:<10}'
    # print(table_format.format('match_sda', 'match_scl'))
    # print('-' * 20)

    # for k in mapping:
    #     if k in match_sda:
    #         print(table_format.format(k, mapping[k]))
    #     else:
    #         print(table_format.format(mapping[k], k))
    to_delete = []
    for i in mapping:
        if mapping[i] != "Missing":
            match.append(mapping[i])
    for i in range(1, len(match)):
        change = match[i] - match[i-1]
        if change == 1:
            to_delete.append(match[i])
    for i in range(len(to_delete)):
        match.remove(to_delete[i])
    print match
    for i in range(len(match)-1):
        print start_decoding_i2c_data[match[i]:match[i+1]:2]
    #     data_final.append("{0:0>2X}".format(
    #             int("".join(map(str, start_decoding_i2c_data[s:s+16:2])), 2)))
    # return data_final
