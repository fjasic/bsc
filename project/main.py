# coding: utf-8
"""
Automating oscilloscope for continuous recording and decoding of CAN, LIN,
I2C,SPI protocols.

python                               2.7.15

Used modules in main.py :
--PyVISA                             1.9.1
--numpy                              1.16.4
--struct
--sys                                2.7.15
--matplotlib                         2.2.4
--warnings
--os
--csv                                1.0
--colorama                           0.4.1
--time
--datetime
"""
import visa
import numpy as np
from struct import unpack
import sys
import matplotlib.pyplot as plt
import warnings
import os
import csv
import colorama
import time as time_global
import datetime
from ssh_spi import ssh_call_spi
from ssh_i2c import ssh_call_i2c
from serial_can import serial_call_can
# from serial_lin import serial_call_lin
from lin_decoding import lin_decoded
from spi_decoding import spi_decoded
from can_decoding import can_decoded
from i2c_decoding import i2c_decoded
from csv_everything import csv_everything_can, csv_everything_i2c, csv_everything_lin,csv_everything_spi
from kmp import KnuthMorrisPratt
# for colors in terminal
colorama.init(autoreset=True)


def main(instrument_id, channel_num, scale, ch_scale, protocol):
    """
    Measures signal from oscilloscope and returns it as 2 lists of
    voltage and time on each trigger.
    --------------------------------------------------------------------------------
    @param instrument_id -- You can see your instrument ID in
    OpenChoiceDesktop application.
    @param channel_num -- Channel from which you read data.[1-4]
    --------------------------------------------------------------------------------
    """

    volts_final = []
    time_final = []
    scope = visa.ResourceManager().open_resource(instrument_id)
    set_channel(scope, str(channel_num))
    scope.write("HORizontal:SCAle" + str(scale))
    scale_readout = float(scope.ask("HORizontal:SCAle?"))
    scope.write("CH"+channel_num+":SCAle " + str(ch_scale))
    scope.write("TRIGger:A SETLevel")
    if protocol == "I2C" or "LIN":
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
            volts[i] = float(volts[i])
        for i in range(len(time)):
            time[i] = float(time[i])
        print "average voltage for CH" + channel_num + \
            ":" + str(sum(volts)/len(volts))
        print "scale for CH" + channel_num + ":" + str(scale_readout)

        return volts, time, scale_readout
    else:
        try:
            scope.write('DATA:WIDTH 1')
            scope.write('DATA:ENC RPB')
            # Start single sequence acquisition
            scope.write("ACQ:STOPA SEQ")
            loop = 0
            while True:
                # increment the loop counter
                loop += 1

                print ".",
                # Arm trigger, then loop until scope has triggered
                scope.write("ACQ:STATE ON")
                while '1' in scope.ask("ACQ:STATE?"):
                    pass
                # save all waveforms, then wait for the waveforms to be written
                ymult = float(scope.ask('WFMPRE:YMULT?'))
                yzero = float(scope.ask('WFMPRE:YZERO?'))
                yoff = float(scope.ask('WFMPRE:YOFF?'))
                xincr = float(scope.ask('WFMPRE:XINCR?'))
                # getting data from oscilloscope
                scope.write('CURVE?')
                data = scope.read_raw()

                headerlen = 2 + int(data[1])
                header = data[:headerlen]
                ADC_wave = data[headerlen:-1]
                ADC_wave = np.array(unpack('%sB' % len(ADC_wave), ADC_wave))
                volts = (ADC_wave - yoff)*ymult + yzero
                time = np.arange(0, xincr*len(volts), xincr)
                print "average voltage for CH" + channel_num + \
                    ":" + str(sum(volts)/len(volts))
                print "scale for CH" + channel_num + ":" + str(scale_readout)
                # for i in range(len(volts)):
                #     volts_final.append(volts[i])
                # for i in range(len(time)):
                #     time[i] = float(time[i]) + 1.0 * (loop-1)
                #     time_final.append(time[i])
        except KeyboardInterrupt:
            # plt.plot(time_final, volts_final)
            # plt.show()
            return volts, time, scale_readout


def set_channel(scope, channel):
    """
    Sets the channel from oscilloscope from which we want to read data.
    -------------------------------------------------------------------
    @param scope -- Object representation of Oscilloscope.
    @param channel -- Number of channel from which the data is read.[1-4]
    -------------------------------------------------------------------
    """
    scope.write('DATA:SOU CH' + str(channel))


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print """USAGE : main.py protocol[CAN,LIN,SPI,I2C] protocol_version(only for LIN)[-c for classic -e for enhanced]"""
        sys.exit()
    instrument_id = 'USB0::0X0699::0x0401::C021046::INSTR'
    # Ignoring FutureWarning.
    warnings.simplefilter(action='ignore', category=FutureWarning)
    print colorama.Fore.YELLOW + "press Ctrl+C to stop measurment"
    # START--------------------------------------------------

    # SPI----------------------------------------------------
    if sys.argv[1] == "SPI":
        # ssh_call_spi()  # Generating SPI signal.
        csv_to_list = []
        time = []
        clock_voltage = []
        data_voltage = []
        sample_period = 5  # Change sample period, look on osclilloscope.
        with open("csv\\spi-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        for i in range(len(csv_to_list)-1):
            time.append(float(csv_to_list[i][0]))
            clock_voltage.append(float(csv_to_list[i][1]))
            data_voltage.append(float(csv_to_list[i][2]))
        # Leveling voltage at 1.0 and 0 depending on raw voltage levels.
        for i in range(len(time)):
            if clock_voltage[i] > 3.0:
                clock_voltage[i] = 1
            else:
                clock_voltage[i] = 0
            if data_voltage[i] > 3.0:
                data_voltage[i] = 1
            else:
                data_voltage[i] = 0
        plt.subplot(2, 1, 1)
        plt.plot(time, clock_voltage)
        plt.subplot(2, 1, 2)
        plt.plot(time, data_voltage)
        plt.show()
        # Decoding spi and returning decoded data.
        data = spi_decoded(clock_voltage, data_voltage, sample_period)
        print "data: " + str(data)
    # END SPI------------------------------------------------

    # CAN----------------------------------------------------
    elif sys.argv[1] == "CAN":
        # serial_call_can() # Generating CAN signal.
        csv_to_list = []
        time_to_decode = []
        can_h = []
        print "if " + colorama.Fore.RED + "red " + \
            colorama.Fore.WHITE + "color shows up,data is not correct"
        print "else " + colorama.Fore.GREEN + "green " + \
            colorama.Fore.WHITE + "it's all good!"
        """getting can frames, only from channel 1 (CAN_H),
        because channel 2 (CAN_L) is mirror of first channel"""
        data_final_can, time_can, period = main(
            instrument_id, "1", 0.004, 1.0000, "CAN")
        sample_rate = int((1 / period)/10)
        plt.xlabel("time")
        plt.ylabel("CAN_H")
        plt.plot(time_can, data_final_can)
        plt.show()
        # Leveling voltage at 1.0 and 0 depending on raw voltage levels.
        for i in range(len(data_final_can)):
            if data_final_can[i] > 3.0:
                data_final_can[i] = 1
            else:
                data_final_can[i] = 0
        print "\n"
        plt.xlabel("time")
        plt.ylabel("CAN_H")
        plt.plot(time_can, data_final_can)
        plt.show()
        csv_everything_can(data_final_can, time_can)
        with open("csv\\can-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        csv_to_list_final = csv_to_list
        for i in range(len(csv_to_list_final)-1):
            time_to_decode.append(float(csv_to_list_final[i][0]))
            can_h.append(float(csv_to_list_final[i][1]))
        inter_frame = []
        if_start = []  # interframe start
        for i in range(28*sample_rate):
            inter_frame.append(0.0)
        for s in KnuthMorrisPratt(can_h, inter_frame):
            if_start.append(s)
        if if_start == []:
            inter_frame = []
            for i in range(27*sample_rate):
                inter_frame.append(0.0)
            for s in KnuthMorrisPratt(can_h, inter_frame):
                if_start.append(s)
            if if_start == []:
                inter_frame = []
                for i in range(26*sample_rate):
                    inter_frame.append(0.0)
                for s in KnuthMorrisPratt(can_h, inter_frame):
                    if_start.append(s)
                if if_start == []:
                    inter_frame = []
                    for i in range(25*sample_rate):
                        inter_frame.append(0.0)
                    for s in KnuthMorrisPratt(can_h, inter_frame):
                        if_start.append(s)
                    if if_start == []:
                        inter_frame = []
                        for i in range(24*sample_rate):
                            inter_frame.append(0.0)
                        for s in KnuthMorrisPratt(can_h, inter_frame):
                            if_start.append(s)
                        print if_start
                        for i in range(len(if_start)-1):
                            can_decoded(can_h[if_start[i]+24*sample_rate:if_start[i+1]+24*sample_rate],
                                        sample_rate)
                    else:
                        for i in range(len(if_start)-1):
                            can_decoded(can_h[if_start[i] + 25*sample_rate:if_start[i+1]+25*sample_rate],
                                        sample_rate)
                else:
                    for i in range(len(if_start)-1):
                        can_decoded(
                            can_h[if_start[i]+26*sample_rate:if_start[i+1]+26*sample_rate], sample_rate)
            else:
                for i in range(len(if_start)-1):
                    can_decoded(
                        can_h[if_start[i]+27*sample_rate:if_start[i+1]+27*sample_rate], sample_rate)
        else:
            for i in range(len(if_start)-1):
                can_decoded(
                    can_h[if_start[i]+28*sample_rate:if_start[i+1]+28*sample_rate], sample_rate)

    # END CAN------------------------------------------------

    # LIN----------------------------------------------------
    elif sys.argv[1] == "LIN":
        # serial_call_lin()  # Generating LIN signal.
        csv_to_list = []
        time_to_decode = []
        lin_voltage_to_decode = []
        data_final_lin, time_lin, sample_period = main(
            instrument_id, "1", 0.001, 5.0000, "LIN")
        plt.xlabel("time")
        plt.ylabel("LIN")
        plt.plot(time_lin, data_final_lin)
        plt.show()
        csv_everything_lin(data_final_lin, time_lin)
        with open("csv\\lin-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        csv_to_list_final = csv_to_list
        for i in range(len(csv_to_list)):
                time_to_decode.append(float(csv_to_list[i][0]))
                lin_voltage_to_decode.append(float(csv_to_list[i][1]))
        for i in range(len(lin_voltage_to_decode)):
            if lin_voltage_to_decode[i] <= 10.0:
                lin_voltage_to_decode[i] = 0
            else:
                lin_voltage_to_decode[i] = 1
        start_of_lin = 0
        for i in range(len(lin_voltage_to_decode)):
            if lin_voltage_to_decode[i] == 0:
                start_of_lin = i
                break
        plt.xlabel("time")
        plt.ylabel("LIN")
        plt.plot(time_lin[start_of_lin:], lin_voltage_to_decode[start_of_lin:])
        plt.show()
        lin_id, lin_parity_bits, lin_data, lin_checksum = lin_decoded(
                lin_voltage_to_decode[start_of_lin:], 50)
        output = "ID: " + str(lin_id) + "||PARITY BITS: " + \
            str(lin_parity_bits) + "||DATA: " + str(lin_data) + \
            "||CHECKSUM: " + str(lin_checksum)
        checksum = 0
        lin_ver = sys.argv[2]
        data = [int(c, 16) for c in lin_data]
        checksum = 0
        hex_int_id = int(lin_id, 16)
        new_int_id = hex_int_id + 0x00
        hex_id = hex(new_int_id)
        final_parity = int(bin(int(hex_id, 16))[2:4])
        if lin_ver == "-e":
            for i in data:
                checksum += i
            checksum += hex_int_id
            if checksum >= 256:
                checksum -= 255
        elif lin_ver == "-c" or hex_int_id == 60 or hex_int_id == 61 or hex_int_id == 62 or hex_int_id == 63:  # frames for diagnostic
            for i in data:
                checksum += i
        else:
            print "not correct lin version protocol(-c for classic[1.1,1.2,1.3] and -e for enhanced[2.0,2.1,2.2])"
            sys.exit()
        print checksum
        checksum = 0xff & (~checksum)
        print checksum
        final_checksum = int(str(hex(checksum))[2:])
        if lin_checksum == final_checksum and final_parity == lin_parity_bits:
            print colorama.Fore.GREEN + output
        elif lin_checksum != final_checksum:
            print colorama.Fore.RED + output + "[CHECKSUM ERROR]"
        elif final_parity != lin_parity_bits:
            print colorama.Fore.RED + output + "[PARITY ERROR]"
        else:
            print colorama.Fore.RED + output + \
                "[PARITY AND CHECKSUM ERROR]"
    # END LIN------------------------------------------------

    # I2C----------------------------------------------------
    elif sys.argv[1] == "I2C":
        # ssh_call_i2c()  # Generating I2C signal.
        csv_to_list = []
        time_to_decode = []
        sda_to_decode = []
        scl_to_decode = []
        sda_i2c, time_i2c, sample_period = main(
            instrument_id, "1", 0.001, 2.0, "I2C")
        scl_i2c, _, sample_period = main(instrument_id, "3", 0.001, 2.0, "I2C")

        sample_rate = int((1 / sample_period)/100)
        plt.subplot(2, 1, 1)
        plt.xlabel("TIME")
        plt.ylabel("SDA")
        plt.plot(time_i2c, sda_i2c)
        plt.subplot(2, 1, 2)
        plt.xlabel("TIME")
        plt.ylabel("SCL")
        plt.plot(time_i2c, scl_i2c)
        plt.show()
        csv_everything_i2c(sda_i2c, scl_i2c, time_i2c)
        with open("csv\\i2c-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        for i in range(len(csv_to_list)-1):
            time_to_decode.append(float(csv_to_list[i][0]))
            scl_to_decode.append(float(csv_to_list[i][1]))
            sda_to_decode.append(float(csv_to_list[i][2]))
        for i in range(len(scl_to_decode)):
            if scl_to_decode[i] >= 3.0:
                scl_to_decode[i] = 1
            else:
                scl_to_decode[i] = 0

        for i in range(len(sda_to_decode)):
            if sda_to_decode[i] >= 3.0:
                sda_to_decode[i] = 1
            else:
                sda_to_decode[i] = 0
        plt.subplot(2, 1, 1)
        plt.xlabel("TIME")
        plt.ylabel("SDA")
        plt.plot(time_to_decode, sda_to_decode)
        plt.subplot(2, 1, 2)
        plt.xlabel("TIME")
        plt.ylabel("SCL")
        plt.plot(time_to_decode, scl_to_decode)
        plt.show()
        i2c_decoded(sda_to_decode, scl_to_decode, 100)
    # END I2C------------------------------------------------
    else:
        print "Supported protocols are SPI,CAN,LIN,I2C!"
        sys.exit()
    sys.exit()
