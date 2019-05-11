import time as Time
import serial
import csv
from TektronixClasses import Tektronix4104
from checksum import checksum
import itertools


def main():
    serial_call()
    try:
        ID = 'USB::0X0699::0x0401::C021046::INSTR'
        oscope = Tektronix4104(ID)
        print "Getting offsets..."
        oscope.getOffsets()
        armed = oscope.armed
        auto = oscope.auto
        ready = oscope.ready
        save = oscope.save
        trigger = oscope.trigger

        print "Checking trigger status..."
        state = oscope.checkTrigger()

        triggerCount = 0
        checkCount = 1
        start = Time.time()
        pw_global_index = 0
        pw_global = 0
        timeTotal = []
        voltageTotal = []
        print "start time: " + str(start)
        while(Time.time() - start < 5):
            # while(True):
            #    if(oscope.state == oscope.trigger):
            print Time.time()
            triggerCount += 1
            print "Scope has triggered %d/%d, reading out data now" % (
                triggerCount, checkCount)
            print "raw data: " + str(oscope.readData())
            [time, volts] = oscope.unpackData()
            timeTotal = time

            voltageTotal = volts
            print "Time: " + str(time) + ";" + "Voltage: " + str(volts)
            if (oscope.state == oscope.auto):
                oscope.setTriggerNorm()

        state = oscope.checkTrigger()
        checkCount += 1
        with open("can-f1ca-ch2-l.csv", "w") as csvFile:
            csvWriter = csv.writer(csvFile)
        for val in itertools.izip(timeTotal, voltageTotal):
            csvWriter.writerow(val)

    except KeyboardInterrupt:
        print "Done taking data."

    finally:
        print "Closing..."
        # oscope.rm.close()

    return 0


def serial_call():
    # data = checksum()
    com3 = serial.Serial(port="COM3", baudrate=115200)
    com4 = serial.Serial(port="COM4", baudrate=115200)
    # com3.write("LIN CLOSE\r\n")
    # com4.write("LIN CLOSE\r\n")
    # com3.write("LIN OPEN FREE 1000\r\n")
    # com4.write("LIN OPEN FREE 1000\r\n")
    # com3.write("LIN TX %s\r\n" % (data))
    # print "Sent LIN TX %s\r\n" % (data)

    com3.write("CAN USER CLOSE CH2\r\n")
    com4.write("CAN USER CLOSE CH2\r\n")

    com3.write("CAN USER OPEN CH2 100K\r\n")
    com4.write("CAN USER OPEN CH2 100K\r\n")
    com4.write("TX2 F1CA\r\n")


if __name__ == "__main__":
    main()
