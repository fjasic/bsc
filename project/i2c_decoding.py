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


def pairwise(it):
    it = iter(it)
    while True:
        yield next(it), next(it)


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
    for i in range(len(scl_to_decode) / sample_period):
        start_decoding_i2c_clock.append(
            int(most_common(scl_to_decode[i * sample_period:i * sample_period + sample_period])))
    data_final = []
    match_sda = []
    match_scl = []
    match = []
    for s in KnuthMorrisPratt(start_decoding_i2c_data, [1, 1, 1, 1, 1, 1]):
        match_sda.append(s)
    for s in KnuthMorrisPratt(start_decoding_i2c_clock, [1, 1, 1, 1, 1, 1, 1]):
        match_scl.append(s)
    mapping = OrderedDict()
    for x in match_scl:
        mapping[x] = x if x in match_sda else 'Missing'

    for x in match_sda:
        mapping[x] = x if x in match_scl else 'Missing'

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
    data_i2c = []
    for current_iter, next_iter in pairwise(match):
        sof = start_decoding_i2c_data[current_iter+5:next_iter:2][1]
        addr_i2c = start_decoding_i2c_data[current_iter+5:next_iter:2][2:9]
        data_i2c.append("{0:0>2X}".format(
                int("".join(map(str, start_decoding_i2c_data[current_iter+5:next_iter:2][11:19])), 2)))
    print data_i2c