# coding: utf-8
"""
Send data for one LIN frame via serial port.

Used modules in serial_lin.py :
--serial
--checksum from my script checksum(checksum.py)
"""
import serial
from checksum import checksum


"""
Send data for one LIN frame via serial port.
"""
lin_data = "filipjas"
lin_id = "50"
lin_version = "2.0"
data = checksum(lin_data, lin_id, lin_version)
print data
# com3 = serial.Serial(port="COM3", baudrate=115200)
com4 = serial.Serial(port="COM4", baudrate=115200)
# com3.write("LIN CLOSE\r\n")
com4.write("LIN CLOSE\r\n")
# com3.write("LIN OPEN FREE 1000\r\n")
com4.write("LIN OPEN FREE 1000\r\n")
for i in range(1000):
    com4.write("LIN TX %s\r\n" % (data))
