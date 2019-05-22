import sys


def checksum(lin_data, lin_id, lin_version):
    data = [ord(c) for c in lin_data]
    print "Hex representation of string:",
    for i in data:
        print hex(i),
    print " "
    chcksum = 0
    if lin_version == "2.0":
        for i in data:
            chcksum += i
            if chcksum >= 256:
                chcksum -= 255
    elif lin_version == "1.3":
        for i in data:
            chcksum += i
    else:
        print "You have not entered correct version of lin protocol[1.3 , 2.0]"
    chcksum = 0xff & (~chcksum)
    print "Checksum: " + hex(chcksum)
    id_string = str(bin(int(lin_id, 16))[2:].zfill(8))
    print "LIN ID: " + id_string
    id = [ord(c) for c in id_string]
    p0 = id[0] ^ id[1] ^ id[2] ^ id[4]
    p1 = not(id[1] ^ id[3] ^ id[4] ^ id[5])
    if p1 is True:
        p1 = 1
    else:
        p1 = 0
    output = ""
    print "PARITY: 0b" + str(p1) + str(p0)
    for i in data:
        output += str(hex(i))[2:]
        output += " "
    return str(output + str(hex(chcksum))[2:])
