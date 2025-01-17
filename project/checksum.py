# coding: utf-8
"""
Calculate checksum, parity and returns output for LIN signal
Used in checksum.py :
--sys                                2.7.15
"""
import sys


def checksum(lin_data, lin_id, lin_version):
    """
    Calculate checksum, parity and returns output for LIN signal
    ------------------------------------------------------------
    @param lin_data -- Data which we want to send on LIN bus.
    @param lin_id -- ID of frame which we want to send on LIN bus.
    @param lin_version -- Used version of LIN(2.0 or 1.0).
    ------------------------------------------------------------
    """
    print "version:" + str(lin_version)
    data = [ord(c) for c in lin_data]
    print "data:",
    for i in data:
        print hex(i),
    print " "
    chcksum = 0
    if lin_version == "1.3":
        for i in data:
            chcksum += int(hex(i), 16)
            if chcksum >= 256:
                chcksum -= 255
    else:
        for i in data:
            chcksum += int(hex(i), 16)
            if chcksum >= 256:
                chcksum -= 255
    chcksum += int(hex(lin_id), 16)
    if chcksum >= 256:
        chcksum -= 255
    chcksum = 0xff & (~chcksum)
    print "checksum: " + hex(chcksum)
    id_string = str(bin(lin_id)[2:].zfill(8))[::-1]
    if lin_version == "1.3":
        print "id[ID0-ID3]: " + str(hex(int(id_string[:4], 2)))
    else:
        print "id[ID0-ID5]: " + str(hex(int(id_string[:6], 2)))
    id = [ord(c) for c in id_string]
    p0 = id[0] ^ id[1] ^ id[2] ^ id[4]
    p1 = not(id[1] ^ id[3] ^ id[4] ^ id[5])
    if p1 is True:
        p1 = 1
    else:
        p1 = 0
    output = ""

    print "parity: 0b" + str(p1) + str(p0)
    for i in data:
        output += str(hex(i))[2:]
        output += " "
    return (str(hex(lin_id))[2:] + " " + output + str(hex(chcksum))[2:])
