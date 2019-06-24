# coding: utf-8
"""
Decodes CAN signal,returns decoded data and calculates Cyclic redundancy check.
Used modules in can_decoding.py :
--matplotlib                         2.2.4
--collections
--kmp from my script KnuthMorrisPratt(kmp.py)
--colorama                           0.4.1
"""
from collections import Counter
import matplotlib.pyplot as plt
from kmp import KnuthMorrisPratt
import colorama
# For colors in terminal.
colorama.init(autoreset=True)


def most_common(lst):
    """
    Return the most common element from list.
    -----------------------------------------
    @param lst -- List from which most common element is found.
    -----------------------------------------
    """
    return max(set(lst), key=lst.count)


def can_decoded(voltage_high, sample_interval):
    """
    Decodes CAN signal from raw voltage and sample interval.
    -----------------------------------------
    @param voltage_high -- Voltage of CAN_H.
    @param sample_interval -- Sample interval of CAN_H.
    -----------------------------------------
    """
    start_decoding_voltage_high = []
    # Reversing waveform.
    for i in range(len(voltage_high) / sample_interval):
        if int(most_common(voltage_high[i * sample_interval:i * sample_interval + sample_interval])) == 0:
            start_decoding_voltage_high.append(1)
        else:
            start_decoding_voltage_high.append(0)
    for_deletion = []

    # Bit stuffing removal.
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [0, 0, 0, 0, 0, 1]):
        for_deletion.append(s)
    for s in KnuthMorrisPratt(start_decoding_voltage_high, [1, 1, 1, 1, 1, 0]):
        for_deletion.append(s)
    iteration = 0
    while iteration < len(for_deletion):
        del start_decoding_voltage_high[for_deletion[iteration]+5-iteration]
        iteration += 1
    ide = start_decoding_voltage_high[13]
    if ide == 0:
        sof = start_decoding_voltage_high[0]
        id_can = start_decoding_voltage_high[1:12]
        rtr = start_decoding_voltage_high[12]
        reserved_bits = start_decoding_voltage_high[14]

        length_can = int(
            "".join(map(str, start_decoding_voltage_high[15:19])), 2)
        data_can = start_decoding_voltage_high[19:19+8*length_can]
        data_can_hex = []
        for i in range(length_can):
            data_can_hex.append("{0:0>2X}".format(
                int("".join(map(str, start_decoding_voltage_high[19+i*8:19+i*8+8])), 2)))
        crc_can = start_decoding_voltage_high[19 + 8*length_can:19+8*length_can+15]
        for_crc = start_decoding_voltage_high[:19+8*length_can]
        # Printing.
        print colorama.Fore.GREEN + "id(standard): " + \
            "{0:0>2X}".format(int("".join(map(str, id_can)), 2)),
        print colorama.Fore.GREEN + "||length: " + str(length_can),
        print colorama.Fore.GREEN + "||data: " + str(data_can_hex),
        print colorama.Fore.GREEN + "||crc: " + str(crc_can)
        crc = []
        result_crc = []
        for i in range(15):
            crc.append(0)
            result_crc.append(0)
        for i in range(len(for_crc)):
            doInvert = (for_crc[i] == 1) ^ crc[14]
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
                result_crc[14-i] = 1
            else:
                result_crc[14-i] = 0
        if crc_can == result_crc:
            # Printing.
            print colorama.Fore.GREEN + "id(standard): " + \
                "{0:0>2X}".format(int("".join(map(str, id_can)), 2)),
            print colorama.Fore.GREEN + "||length: " + str(length_can),
            print colorama.Fore.GREEN + "||data: " + str(data_can_hex),
            print colorama.Fore.GREEN + "||crc: " + str(crc_can)
        else:
            print colorama.Fore.RED + "id(standard): " + \
                "{0:0>2X}".format(int("".join(map(str, id_can)), 2)),
            print colorama.Fore.RED + "||length: " + str(length_can),
            print colorama.Fore.RED + "||data: " + str(data_can_hex),
            print colorama.Fore.RED + "||crc: " + str(crc_can)
    else:
        sof = start_decoding_voltage_high[0]
        id_can_a = start_decoding_voltage_high[1:12]
        srr = start_decoding_voltage_high[12]
        id_can_b = start_decoding_voltage_high[14:32]

        rtr = start_decoding_voltage_high[32]
        reserved_bits = start_decoding_voltage_high[33:35]
        length_can = int(
            "".join(map(str, start_decoding_voltage_high[35:39])), 2)
        data_can = start_decoding_voltage_high[39:39+8*length_can]
        data_can_hex = []
        for i in range(length_can):
            data_can_hex.append("{0:0>2X}".format(
                int("".join(map(str, start_decoding_voltage_high[39+i*8:39+i*8+8])), 2)))
        crc_can = start_decoding_voltage_high[39 + 8*length_can:39+ 8*length_can+15]
        for_crc = start_decoding_voltage_high[:39+8*length_can]
        crc = []
        result_crc = []
        for i in range(15):
            crc.append(0)
            result_crc.append(0)
        for i in range(len(for_crc)):
            doInvert = (for_crc[i] == 1) ^ crc[14]
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
                result_crc[14-i] = 1
            else:
                result_crc[14-i] = 0
        if crc_can == result_crc:
            # Printing.
            print colorama.Fore.GREEN + "id_A(extended): " + \
                "{0:0>2X}".format(int("".join(map(str, id_can_a)), 2)),
            print colorama.Fore.GREEN + "id_B(extended): " + \
                "{0:0>2X}".format(int("".join(map(str, id_can_b)), 2)),
            print colorama.Fore.GREEN + "||length: " + str(length_can),
            print colorama.Fore.GREEN + "||data: " + str(data_can_hex),
            print colorama.Fore.GREEN + "||crc: " + str(crc_can)
        else:
            print colorama.Fore.RED + "id(standard): " + \
                "{0:0>2X}".format(int("".join(map(str, id_can_a)), 2)),
            print colorama.Fore.RED + "id_B(extended): " + \
                "{0:0>2X}".format(int("".join(map(str, id_can_b)), 2)),
            print colorama.Fore.RED + "||length: " + str(length_can),
            print colorama.Fore.RED + "||data: " + str(data_can_hex),
            print colorama.Fore.RED + "||crc: " + str(crc_can)
