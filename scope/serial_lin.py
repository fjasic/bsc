import serial
import checksum


def serial_call_lin():
    # lin_data = "FILIP"
    # lin_id = "50"
    # lin_version = "2.0"
    # data = checksum(lin_data, lin_id, lin_version)
    # print data
    # com3 = serial.Serial(port="COM3", baudrate=115200)
    com4 = serial.Serial(port="COM4", baudrate=115200)
    # com3.write("LIN CLOSE\r\n")
    com4.write("LIN CLOSE\r\n")
    # com3.write("LIN OPEN FREE 1000\r\n")
    com4.write("LIN OPEN FREE 20000\r\n")
    # com3.write("LIN TX %s\r\n" % (data))
    # print "Sent LIN TX %s\r\n" % (data)
    # print "Sent LIN TX 66 69 6c 69 70\r\n"
