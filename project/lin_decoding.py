# coding: utf-8
"""
Decodes LIN signal and returns decoded data.
Used modules in lin_decoding.py :
--collections
"""
from collections import Counter


def most_common(lst):
    """
    Return the most common element from list.
    -----------------------------------------
    @param lst -- List from which most common element is found.
    -----------------------------------------
    """
    return max(set(lst), key=lst.count)


def lin_decoded(voltage, sample_interval, lin_version):
    """
    Decodes LIN signal from raw voltage and sample interval.
    -----------------------------------------
    @param voltage -- Voltage of LIN.
    @param sample_interval -- Sample rate of oscilloscope.
    -----------------------------------------
    """
    decoded_lin = []
    for i in range(len(voltage) / sample_interval):
        decoded_lin.append(
            int(most_common(voltage[i * sample_interval:i * sample_interval + sample_interval])))
    results = []
    sync_break = decoded_lin[0:13]
    sync_field = decoded_lin[15:22]
    sync_field_to_hex = ""
    for i in range(len(sync_field)):
        sync_field_to_hex += str(sync_field[i])
    sync_field_hex = "{0:0>2X}".format(int(sync_field_to_hex, 2))
    rest_of_lin = decoded_lin[25:len(decoded_lin)]
    id_field = ""
    parity_bits = ""
    data_field = []
    id_field = "{0:0>2X}".format(
        int("".join(map(str, decoded_lin[25:33][::-1])), 2))
    if lin_version == "-e":
        pid = "{0:0>2X}".format(
            int("".join(map(str, decoded_lin[25:31][::-1])), 2))
    else:
        pid = "{0:0>2X}".format(
            int("".join(map(str, decoded_lin[25:29][::-1])), 2))
    parity_bits = "{0:b}".format(
        int("".join(map(str, decoded_lin[25:33][::-1])), 2))[0:2]
    length = 0
    if int(pid, 16) >= 0 and int(pid, 16) < 31:
        length = 2
    elif int(pid, 16) >= 32 and int(pid, 16) < 47:
        length = 4
    else:
        length = 8
    for x in range(length):
        data_field.append("{0:0>2X}".format(
            int("".join(map(str, decoded_lin[(35 + (x * 10)):(43 + (x * 10))][::-1])), 2)))
    checksum = "{0:0>2X}".format(
        int("".join(map(str, decoded_lin[(35 + (length * 10)):(43 + (length * 10))][::-1])), 2))
    return id_field, int(parity_bits), data_field, checksum
