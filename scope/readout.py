import visa
import numpy as np
from struct import unpack
import pylab
import sys
import ripyl
import ripyl.protocol.spi as spi
import ripyl.streaming as stream
from collections import OrderedDict
import ripyl.util.plot as rplot
from ssh_spi import ssh_call_spi
# from serial_lin import serial_call_lin
from csv_output import *
import warnings


def main(instrument_id, channel_num):
    scope = visa.ResourceManager().open_resource(instrument_id)
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
    time = np.arange(0, xincr*len(volts), xincr)
    return volts, time


def set_channel(scope, channel):
    scope.write('DATA:SOU CH'+str(channel))


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print "USAGE : readout.py --protocol[CAN,LIN,SPI,I2C] --data_channel[1,2,3,4] --clock_channel[1,2,3,4](only for SPI and I2C)"
        sys.exit()
    # YOU CAN SEE YOUR INSTRUMENT ID IN OpenChoiceDesktop APPLICATION
    instrument_id = 'USB0::0X0699::0x0401::C021046::INSTR'
    warnings.simplefilter(action='ignore', category=FutureWarning)
    # SAMPLE PERIOD IS 0.0000004 FOR TEKTRONIX DPO4104
    sample_period = 0.0000004
    # START--------------------------------------------------
    # serial_call_lin()
    # serial_call_can()
    # ssh_call_spi()
    # ssh_call_i2c()

    # SPI----------------------------------------------------
    if sys.argv[1] == "SPI":
        # GENERISANJE SPI SIGNALA
        # ssh_call_spi()
        ##########################
        ##########################
        # OBRADA SPI SIGNALA
        spi_ch_data = sys.argv[2]
        spi_ch_clock = sys.argv[3]
        if int(spi_ch_data) > 4 or int(spi_ch_clock) > 4:
            print "Works only for oscilloscopes with 4 channels maximum"
            sys.exit()
        data_final_spi, time = main(instrument_id, spi_ch_data)
        clock_final_spi, time = main(instrument_id, spi_ch_clock)
        csv_everything_spi(data_final_spi, clock_final_spi, time)
        data = list(ripyl.streaming.samples_to_sample_stream(
            data_final_spi, sample_period))
        clock = list(ripyl.streaming.samples_to_sample_stream(
            clock_final_spi, sample_period))
        records = list(spi.spi_decode(
            iter(clock), iter(data), lsb_first=False))
        channels = OrderedDict([('CLK (V)', clock), ('MOSI (V)', data)])
        plotter = rplot.Plotter()
        plotter.plot(channels, records)
        pylab.get_current_fig_manager().resize(
            *pylab.get_current_fig_manager().window.maxsize())
        plotter.show()
        print "SPI - PLOT done"
        plotter.save_plot("decoded-SPI.png")
        print "SPI - PNG output done"
        print "Exit figure to end program..."
    # END SPI------------------------------------------------

    # CAN----------------------------------------------------
    elif sys.argv[1] == "CAN":
        # serial_call_can()
        pass
    # END CAN------------------------------------------------

    # LIN----------------------------------------------------
    elif sys.argv[1] == "LIN":
        # GENERISANJE LIN SIGNALA
        # lin_data = "FILIP"
        # lin_id = "50"
        # lin_version = "2.0"
        # serial_call_lin()
        #########################
        #########################
        # OBRADA LIN SIGNALA
        lin_ch_data = sys.argv[2]
        if int(lin_ch_data) > 4:
            print "Works only for oscilloscopes with 4 channels maximum"
            sys.exit()
        data_final_lin, time = main(instrument_id, lin_ch_data)
        index_start_lin = 0

        for i in range(len(data_final_lin)):
            if data_final_lin[i] < 10.0:
                index_start_lin = i
                break
        data_lin = data_final_lin[index_start_lin:]
        time_lin = time[index_start_lin:]
        for i in range(len(data_lin)):
            if data_lin[i] <= 2.0:
                data_lin[i] = 0
            else:
                data_lin[i] = 1
        data_lin[0] = 0
        pylab.ylabel("data")
        pylab.xlabel("time")

        pylab.plot(time_lin, data_lin, color="r")
        pylab.show()
        # records = lin_decoded()
        csv_everything_lin(data_lin, time_lin)
        # print records

    # END LIN------------------------------------------------

    # I2C----------------------------------------------------
    elif sys.argv[1] == "I2C":
        # ssh_call_i2c()
        i2c_ch_data = sys.argv[2]
        i2c_ch_clock = sys.argv[3]
        if int(i2c_ch_data) > 4 or int(i2c_ch_clock) > 4:
            print "Works only for oscilloscopes with 4 channels maximum"
            sys.exit()
        print "I2C - PLOT done"
        plotter.save_plot("decoded-I2C.png")
        print "I2C - PNG output done"
        print "Exit figure to end program..."
    # END I2C------------------------------------------------
    else:
        print "Supported protocols are SPI,CAN,LIN,I2C!"
        sys.exit()
    sys.exit()
