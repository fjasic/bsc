import time as Time
import pylab
import matplotlib.pyplot as plt
from TektronixClasses import Tektronix4104


def main():
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
        timeTotal = []
        voltageTotal = []
        counter = 30
        print "start time: " + str(start)
        while(Time.time() - start < 1):
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
            counter -= 1

        state = oscope.checkTrigger()
        checkCount += 1
        for i, v in enumerate(voltageTotal):
            if v < 0.1:
                pw = i
                if voltageTotal[i] > 2.3:
                    print "FREKVENCIJA: " + str(1/(timeTotal[i+1])) + "kHz"
                    if voltageTotal[i] < 0.1:
                        t = voltageTotal[i]
                        print "DUTY CYCLE: " + str(pw/t * 100) + "%"
                        break
                        
    except KeyboardInterrupt:
        print "Done taking data."

    finally:
        print "Closing..."
        # oscope.rm.close()

    return 0


if __name__ == "__main__":
    main()
