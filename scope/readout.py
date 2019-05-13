import visa
import numpy as np
from struct import unpack
import pylab
import csv
import itertools
import serial
import sys
import checksum


def main():
    serial_call()
    try:
        scope = visa.ResourceManager().open_resource(
            'USB::0X0699::0x0401::C021046::INSTR')
        scope.write('DATA:SOU CH1')
        scope.write('DATA:WIDTH 1')
        scope.write('DATA:ENC RPB')

        ymult = float(scope.ask('WFMPRE:YMULT?'))
        yzero = float(scope.ask('WFMPRE:YZERO?'))
        yoff = float(scope.ask('WFMPRE:YOFF?'))
        xincr = float(scope.ask('WFMPRE:XINCR?'))

        scope.write('CURVE?')
        data = scope.read_raw()

        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]

        ADC_wave = np.array(unpack('%sB' % len(ADC_wave), ADC_wave))
        volts = (ADC_wave - yoff)*ymult + yzero
        time = np.arange(0, xincr*len(volts), xincr)

        for i in range(len(volts)):
            if volts[i] < 1.0:
                pw_index = i
                break
        reverse_volts = volts[::-1]

        for i in range(len(reverse_volts)):
            if reverse_volts[i] < 2.0:
                pw_index_reverse = i
                break

        pw_index_end = len(volts) - pw_index_reverse
        volt_usefull = volts[pw_index:pw_index_end]
        time_usefull = time[pw_index:pw_index_end]

        with open("can-f1ca-ch2-l.csv", "w") as csvCapture:
            csvWriter = csv.writer(csvCapture)
            for val in itertools.izip(time_usefull, volt_usefull):
                csvWriter.writerow(val)
            print "CSV output done"
            
        pylab.plot(time_usefull, volt_usefull)
        pylab.savefig("can-f1ca-ch2-l.png")
        print "PNG output done"
        print "Exit figure to end program..."
        pylab.show()
    
    except KeyboardInterrupt:
        print "Done taking data."

    finally:
        print "Closing..."
        sys.exit()

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