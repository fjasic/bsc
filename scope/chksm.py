import sys


args = sys.argv[1:]
if len(args) != 3:
    print "usage: chksum.py <string> <id> <lin_ver>"
    sys.exit(1)

ime_string = args[0]
id_unos = args[1]
lin_ver = args[2]

data = [ord(c) for c in ime_string]
print "hex representation of string:",
for i in data:
    print hex(i),
print " "
chcksum = 0
if lin_ver == "2.0":
    for i in data:
        chcksum += i
        if chcksum >= 256:
            chcksum -= 255
else:
    for i in data:
        chcksum += i

chcksum = 0xff & (~chcksum)
print "checksum: " + hex(chcksum)
id_string = str(bin(int(id_unos, 16))[2:].zfill(8))
print "id: " + id_unos
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
print (output + str(hex(chcksum))[2:])