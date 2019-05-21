import visa
import numpy as np
from struct import unpack
import pylab
import csv
import itertools
import serial
import sys
import checksum
import ripyl
import ripyl.protocol.spi as spi
import ripyl.streaming as stream
from collections import OrderedDict
import ripyl.util.plot as rplot
# import sshrpi
"""sve pod komentarom je za CAN"""


def main(channel_num):
    # serial_call()
    # sshrpi()
    scope = visa.ResourceManager().open_resource(
        'USB0::0X0699::0x0401::C021046::INSTR')
    set_channel(scope, str(channel_num))
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
    global time
    time = np.arange(0, xincr*len(volts), xincr)
    data_volts = []
    clock_volts = []
    pylab.title("SPI")
    pylab.figure(1)
    if channel_num == 1:
        # for i in range(len(volts)):
        #     if volts[i] > 3.0:
        #         volts[i] = 1.0
        #     else:
        #         volts[i] = 0.0
        # data_volts = volts
        # plot_1(time, data_volts)
        plot_1(time, volts)
    else:
        # for i in range(len(volts)):
        #     if volts[i] > 0.5:
        #         volts[i] = 1.0
        #     else:
        #         volts[i] = 0.0
        # clock_volts = volts
        # plot_2(time, clock_volts)
        plot_2(time, volts)

    # RAZLIKA IZMEDJU 2 UZORKOVANJA JE 0,000004
    # for i in range(len(volts)):
    #     if volts[i] < 4.80:
    #         pw_index = i
    #         break
    # reverse_volts = volts[::-1]

    # for i in range(len(reverse_volts)):
    #     if reverse_volts[i] < 1.43:
    #         pw_index_reverse = i
    #         break

    # pw_index_end = len(volts) - pw_index_reverse
    # volts_useful = volts[pw_index:pw_index_end]
    # time_useful = time[pw_index:pw_index_end]

    # can_final = []

    # for i in volts_useful[::40]:
    #     can_final.append(int(i))
    # print can_final
    # for i in range(1, 12):
    #     id_base += str(can_final[i])
    # print can_final
    # print len(can_final)
    # print "id:" + str(can_final[1:12])
    return volts


def plot_1(time, data_volts):
    pylab.subplot(2, 1, 1)
    pylab.ylabel("data")
    pylab.xlabel("time")
    pylab.plot(time, data_volts, color="r")


def plot_2(time, clock_volts):
    pylab.subplot(2, 1, 2)
    pylab.xlabel("time")
    pylab.ylabel("clock")
    pylab.plot(time, clock_volts)


def plot_everything():
    pylab.get_current_fig_manager().resize(
        *pylab.get_current_fig_manager().window.maxsize())
    pylab.savefig("SPI_scope_output.png")
    pylab.show()


def csv_everything(data_final, clock_final):
    with open("spi-capture.csv", "w") as csvCapture:
        csvWriter = csv.writer(csvCapture)
        for val in itertools.izip(time, clock_final, data_final):
            csvWriter.writerow(val)
    print "CSV output done"


def set_channel(scope, channel):
    scope.write('DATA:SOU CH'+str(channel))

# def serial_call():
#     # data = checksum()
#     com3 = serial.Serial(port="COM3", baudrate=115200)
#     com4 = serial.Serial(port="COM4", baudrate=115200)
#     # com3.write("LIN CLOSE\r\n")
#     # com4.write("LIN CLOSE\r\n")
#     # com3.write("LIN OPEN FREE 1000\r\n")
#     # com4.write("LIN OPEN FREE 1000\r\n")
#     # com3.write("LIN TX %s\r\n" % (data))
#     # print "Sent LIN TX %s\r\n" % (data)

#     com3.write("CAN USER CLOSE CH2\r\n")
#     com4.write("CAN USER CLOSE CH2\r\n")
#     com3.write("CAN USER CLOSE CH1\r\n")
#     com4.write("CAN USER CLOSE CH1\r\n")
#     com3.write("CAN USER OPEN CH1 125K\r\n")
#     com4.write("CAN USER OPEN CH1 125K\r\n")
#     com3.write("CAN USER OPEN CH2 125K\r\n")
#     com4.write("CAN USER OPEN CH2 125K\r\n")
#     com4.write("CAN USER MASK CH2 0000\r\n")
#     com4.write("CAN USER FILTER CH2 ")
#     com4.write("CAN USER ALIGN RIGHT\r\n")
#     com4.write("CAN USER TX CH2 AAAA\r\n")


if __name__ == "__main__":
    data_final = main(1)
    clock_final = main(3)
    plot_everything()
    sample_period = 0.0000004
    data = list(ripyl.streaming.samples_to_sample_stream(
        data_final, sample_period))
    clock = list(ripyl.streaming.samples_to_sample_stream(
        clock_final, sample_period))
    records = list(spi.spi_decode(iter(clock), iter(data), lsb_first=False))
    channels = OrderedDict([('CLK (V)', clock), ('MOSI / MISO (V)', data)])
    plotter = rplot.Plotter()
    plotter.plot(channels, records)
    pylab.get_current_fig_manager().resize(
        *pylab.get_current_fig_manager().window.maxsize())
    plotter.show()
    plotter.save_plot("dekodovan-SPI-123.png")
    print "PNG output done"
    print "Exit figure to end program..."
    csv_everything(data_final, clock_final)
