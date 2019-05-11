import time as Time
import serial
import csv
from TektronixClasses import Tektronix4104
from checksum import *
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
        global voltageTotal
        global timeTotal
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
        csvFile = open("can-f1ca-ch2-l.csv", "w")
        csvWriter = csv.writer(csvFile)
        for val in itertools.izip(timeTotal, voltageTotal):
            csvWriter.writerow(val)
        csvFile.close()
        # pulse_width()
        # print_res()

    except KeyboardInterrupt:
        print "Done taking data."

    finally:
        print "Closing..."
        # oscope.rm.close()

    return 0


def serial_call():
    #data = checksum()
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


def print_res():
    for i in range(pw_global_index, len(voltageTotal)):
        if voltageTotal[i] > 2.0:
            t = timeTotal[i]
            print "FREQ: " + str(1/t) + " Hz"
            print "DUTY CYCLE: " + str((pw_global/t) * 100) + "%"
            break


def pulse_width():
    for i, v in enumerate(voltageTotal):
        if v < 0.1:
            global pw_global_index
            pw_global_index = i
            global pw_global
            pw_global = timeTotal[i] - timeTotal[0]
            break


if __name__ == "__main__":
    main()
