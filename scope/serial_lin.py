import serial
from checksum import checksum


def serial_call_lin():
    lin_data = "f"
    lin_id = "00"
    lin_version = "1.3"
    data = checksum(lin_data, lin_id, lin_version)
    com3 = serial.Serial(port="COM3", baudrate=115200)
    com4 = serial.Serial(port="COM4", baudrate=115200)
    com3.write("LIN CLOSE\r\n")
    com4.write("LIN CLOSE\r\n")
    com3.write("LIN OPEN FREE 1000\r\n")
    com4.write("LIN OPEN FREE 1000\r\n")
    com4.write("LIN TX %s\r\n" % (data))
    print "Sent LIN TX %s\r\n" % (data)
