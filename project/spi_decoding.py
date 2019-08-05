# coding: utf-8
"""
Decodes SPI signal and returns decoded data.
Used modules in spi_decoding.py :
--collections
--kmp from my script KnuthMorrisPratt(kmp.py)
"""
from collections import Counter
from kmp import KnuthMorrisPratt


def most_common(lst):
    """
    Return the most common element from list.
    -----------------------------------------
    @param lst -- List from which most common element is found.
    -----------------------------------------
    """
    return max(set(lst), key=lst.count)


def spi_decoded(voltage_clock, voltage_data, sample_interval):
    """
    Decodes SPI signal from raw voltage and sample interval.
    -----------------------------------------
    @param voltage_data -- Voltage of MOSI/MISO.
    @param voltage_clock -- Voltage of SCLK.
    @param sample_interval -- Sample rate of oscilloscope.
    -----------------------------------------
    """
    star_decodig_spi_data = []
    start_decoding_spi_data = []
    for i in range(len(voltage_data) / sample_interval):
        star_decodig_spi_data.append(
            int(most_common(voltage_data[i * sample_interval:i * sample_interval + sample_interval])))
        start_decoding_spi_data.append(
            int(most_common(voltage_clock[i * sample_interval:i * sample_interval + sample_interval])))
    data_final = []
    for s in KnuthMorrisPratt(start_decoding_spi_data, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]):
        data_final.append("{0:0>2X}".format(
            int("".join(map(str, star_decodig_spi_data[s:s+16:2])), 2)))
    return data_final
