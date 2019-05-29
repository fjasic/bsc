import serial


def serial_call_can():
    com3 = serial.Serial(port="COM3", baudrate=115200)
    com4 = serial.Serial(port="COM4", baudrate=115200)
    com3.write("CAN USER CLOSE CH2\r\n")
    com4.write("CAN USER CLOSE CH2\r\n")
    com3.write("CAN USER CLOSE CH1\r\n")
    com4.write("CAN USER CLOSE CH1\r\n")
    com3.write("CAN USER OPEN CH1 50K\r\n")
    com4.write("CAN USER OPEN CH1 50K\r\n")
    com3.write("CAN USER OPEN CH2 50K\r\n")
    com4.write("CAN USER OPEN CH2 50K\r\n")
    com4.write("CAN USER MASK CH2 0000\r\n")
    com4.write("CAN USER FILTER CH2 ")
    com4.write("CAN USER ALIGN RIGHT\r\n")
    com4.write("CAN USER TX CH2 ffff\r\n")
