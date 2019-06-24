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
# from serial_can import serial_call_can
# from serial_lin import serial_call_lin
from lin_decoding import lin_decoded
from spi_decoding import spi_decoded
from can_decoding import can_decoded
from i2c_decoding import i2c_decoded
from csv_everything import csv_everything_can, csv_everything_i2c, csv_everything_lin, csv_everything_spi
from kmp import KnuthMorrisPratt
# for colors in terminal
colorama.init(autoreset=True)


class Signal:
    def __init__(self, time, voltage):
        self.time = time
        self.voltage = voltage

    def plotting_1_ch(self, x_label, y_label):
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.plot(self.time, self.voltage)
        plt.show()

    def plotting_2_ch(self, data_ch, clock_ch, x_label_data, y_label_data, x_label_clock, y_label_clock):
        plt.subplot(2, 1, 1)
        plt.xlabel(x_label_data)
        plt.ylabel(y_label_data)
        plt.plot(data_ch.time, data_ch.voltage)
        plt.subplot(2, 1, 2)
        plt.xlabel(x_label_clock)
        plt.ylabel(y_label_clock)
        plt.plot(clock_ch.time, clock_ch.voltage)
        plt.show()

    def level_out_signal(self, leveling_value):
        for i in range(len(self.voltage)):
            if self.voltage[i] >= leveling_value:
                self.voltage[i] = 1
            else:
                self.voltage[i] = 0
        return self.voltage


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

    volts_cumulative = []
    time_cumulative = []
    scope = visa.ResourceManager().open_resource(instrument_id)
    set_channel(scope, str(channel_num))
    scope.write("HORizontal:SCAle" + str(scale))
    scale_readout = float(scope.ask("HORizontal:SCAle?"))
    scope.write("CH"+channel_num+":SCAle " + str(ch_scale))
    scope.write("TRIGger:A SETLevel")
    if protocol == "I2C" or "SPI":
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
                # Increment the loop counter
                loop += 1
                print ".",
                # Arm trigger, then loop until scope has triggered
                scope.write("ACQ:STATE ON")
                while '1' in scope.ask("ACQ:STATE?"):
                    pass
                # Save all waveforms, then wait for the waveforms to be written
                ymult = float(scope.ask('WFMPRE:YMULT?'))
                yzero = float(scope.ask('WFMPRE:YZERO?'))
                yoff = float(scope.ask('WFMPRE:YOFF?'))
                xincr = float(scope.ask('WFMPRE:XINCR?'))
                # Getting data from oscilloscope
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
                for i in range(len(volts)):
                    volts_cumulative.append(volts[i])
                for i in range(len(time)):
                    time[i] = float(time[i]) + 1.0 * (loop-1)
                    volts_cumulative.append(time[i])
        except KeyboardInterrupt:
            plt.plot(volts_cumulative, volts_cumulative)
            plt.show()
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


def recursion_frame_check(can_voltage, if_start, inter_frame, sample_rate, length):
    for i in range(length*sample_rate):
        inter_frame.append(0.0)
    for s in KnuthMorrisPratt(can_voltage, inter_frame):
        if_start.append(s)
    if if_start == []:
        inter_frame = []
        recursion_frame_check(inter_frame, sample_rate, length-1)
    else:
        for i in range(len(if_start)-1):
            can_decoded(
                can_voltage[if_start[i]+length*sample_rate:if_start[i+1]+length*sample_rate], sample_rate)


def lin_processing(time_to_decode, lin_voltage_to_decode, lin_ver):
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
    # plt.xlabel("time")
    # plt.ylabel("LIN")
    # plt.plot(time_to_decode[start_of_lin:],
    #          lin_voltage_to_decode[start_of_lin:])
    # plt.show()
    lin_id, lin_parity_bits, lin_data, lin_checksum = lin_decoded(
        lin_voltage_to_decode[start_of_lin:], 50, lin_ver)
    output = "ID: " + str(lin_id) + "||PARITY BITS: " + \
        str(lin_parity_bits) + "||DATA: " + str(lin_data) + \
        "||CHECKSUM: " + str(lin_checksum)
    checksum = 0
    data = [int(c, 16) for c in lin_data]
    checksum = 0
    hex_int_id = int(lin_id, 16)
    new_int_id = hex_int_id + 0x00
    hex_id = hex(new_int_id)
    final_parity = int(bin(int(hex_id, 16))[2:4])
    measurent_lin_checksum = int(lin_checksum, 16)
    if lin_ver == "-e":
        for i in data:
            checksum += i
            if checksum >= 256:
                checksum -= 255
        checksum += int(lin_id, 16)
        if checksum >= 256:
            checksum -= 255
    elif lin_ver == "-c" or hex_int_id == 60 or hex_int_id == 61 or hex_int_id == 62 or hex_int_id == 63:  # frames for diagnostic
        for i in data:
            checksum += i
            if checksum >= 256:
                checksum -= 255
    else:
        print "not correct lin version protocol(-c for classic[1.1,1.2,1.3] and -e for enhanced[2.0,2.1,2.2])"
        sys.exit()
    checksum = 0xff & (~checksum)
    if checksum == measurent_lin_checksum and checksum == measurent_lin_checksum:
        print colorama.Fore.GREEN + output
    elif checksum != measurent_lin_checksum:
        print colorama.Fore.RED + output + "[CHECKSUM ERROR]"
    elif checksum != measurent_lin_checksum:
        print colorama.Fore.RED + output + "[PARITY ERROR]"
    else:
        print colorama.Fore.RED + output + \
            "[PARITY AND CHECKSUM ERROR]"


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 5:
        print """USAGE : main.py protocol[CAN,LIN,SPI,I2C] protocol_version(only for LIN)[-c for classic -e for enhanced] mode[online/offline]"""
        sys.exit()
    instrument_id = 'USB0::0X0699::0x0401::C021046::INSTR'
    # Ignoring FutureWarning.
    warnings.simplefilter(action='ignore', category=FutureWarning)
    print colorama.Fore.YELLOW + "press Ctrl+C to stop measurment"
    # START--------------------------------------------------

    # SPI----------------------------------------------------
    if sys.argv[1] == "SPI":
        # ssh_call_spi()  # Generating SPI signal.
        mode = sys.argv[2]
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
        # TODO implement leveling,change readout function
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
        mode = sys.argv[2]
        print "if " + colorama.Fore.RED + "red " + \
            colorama.Fore.WHITE + "color shows up,data is not correct"
        print "else " + colorama.Fore.GREEN + "green " + \
            colorama.Fore.WHITE + "it's all good!"
        """getting can frames, only from channel 1 (CAN_H),
		because channel 2 (CAN_L) is mirror of first channel"""
        if mode == "online":
            voltage_can_scope, time_can_scope, period = main(
                instrument_id, "1", 0.004, 1.0000, "CAN")
            sample_rate = int((1 / period)/10)
            can_online_before_leveling = Signal(
                time_can_scope, voltage_can_scope)
            can_online_before_leveling.plotting_1_ch("TIME", "CAN_H")
            # Leveling voltage at 1.0 and 0 depending on raw voltage levels.
            # TODO implement leveling
            for i in range(len(voltage_can_scope)):
                if voltage_can_scope[i] > 3.0:
                    voltage_can_scope[i] = 1
                else:
                    voltage_can_scope[i] = 0
            can_online = Signal(time_can_scope, voltage_can_scope)
            can_online.plotting_1_ch("TIME", "CAN_H")
            csv_everything_can(can_online.time, can_online.voltage)
            recursion_frame_check(
                can_online.voltage, inter_frame, if_start, sample_rate, 28)
        else:
            csv_to_list = []
            time_can_csv = []
            voltage_can_csv = []
            with open("csv\\can-capture.csv", "r") as csvCapture:
                reader = csv.reader(csvCapture)
                for row in reader:
                    csv_to_list.append(row)
            csv_to_list_final = csv_to_list
            for i in range(len(csv_to_list_final)-1):
                time_can_csv.append(float(csv_to_list_final[i][0]))
                voltage_can_csv.append(float(csv_to_list_final[i][1]))
            can_offline = Signal(time_can_csv, voltage_can_csv)
            can_offline.plotting_1_ch("TIME", "CAN_H")

            inter_frame = []
            if_start = []  # interframe start
            sample_rate = 25
            recursion_frame_check(can_offline.voltage, inter_frame,
                                  if_start, sample_rate, 28)

    # END CAN------------------------------------------------

    # LIN----------------------------------------------------
    elif sys.argv[1] == "LIN":
        # serial_call_lin()  # Generating LIN signal.
        if len(sys.argv) < 4:
            print """USAGE : main.py protocol[CAN,LIN,SPI,I2C] protocol_version(only for LIN)[-c for classic -e for enhanced] mode[online/offline]"""
            sys.exit()
        lin_ver = sys.argv[2]
        mode = sys.argv[3]
        if mode == "online":
            data_lin_scope, time_lin_scope, sample_period = main(
                instrument_id, "1", 0.001, 5.0000, "LIN")
            lin_online = Signal(time_lin_scope, data_lin_scope)
            lin_online.plotting_1_ch("TIME", "LIN")
            csv_everything_lin(lin_online.time, lin_online.voltage)
            lin_processing(lin_online.time, lin_online.voltage, lin_ver)

        else:
            csv_to_list = []
            time_lin_csv = []
            lin_voltage_csv = []
            with open("csv\\lin-capture.csv", "r") as csvCapture:
                reader = csv.reader(csvCapture)
                for row in reader:
                    csv_to_list.append(row)
            csv_to_list_final = csv_to_list
            for i in range(len(csv_to_list)):
                time_lin_csv.append(float(csv_to_list[i][0]))
                lin_voltage_csv.append(float(csv_to_list[i][1]))
            lin_offline = Signal(time_lin_csv, lin_voltage_csv)
            lin_offline.plotting_1_ch("TIME", "LIN")
            lin_processing(lin_offline.time, lin_offline.voltage, lin_ver)
    # END LIN------------------------------------------------

    # I2C----------------------------------------------------
    elif sys.argv[1] == "I2C":
        # ssh_call_i2c()  # Generating I2C signal.
        mode = sys.argv[2]
        if mode == "online":
            sda_i2c, time_i2c, sample_period = main(
                instrument_id, "1", 0.001, 2.0, "I2C")
            scl_i2c, _, sample_period = main(
                instrument_id, "3", 0.001, 2.0, "I2C")
            sample_rate = int((1 / sample_period)/100)
            i2c_clock_online = Signal(time_i2c, scl_i2c)
            i2c_data_online = Signal(time_i2c, sda_i2c)
            Signal().plotting_2_ch(i2c_data_online, i2c_clock_online, "SDA", "TIME", "SCL", "TIME")
            csv_everything_i2c(time, i2c_data_online.voltage,
                               i2c_clock_online.voltage)
            for i in range(len(i2c_clock_online.voltage)):
                if i2c_clock_online.voltage[i] >= 3.0:
                    i2c_clock_online.voltage[i] = 1
                else:
                    i2c_clock_online.voltage[i] = 0

            for i in range(len(i2c_data_online.voltage)):
                if i2c_data_online.voltage[i] >= 3.0:
                    i2c_data_online.voltage[i] = 1
                else:
                    i2c_data_online.voltage[i] = 0
            Signal().plotting_2_ch(i2c_data_online, i2c_clock_online, "SDA", "TIME", "SCL", "TIME")
            i2c_decoded(i2c_data_online.voltage, i2c_clock_online.voltage, 100)
        else:
            csv_to_list = []
            time_i2c_csv = []
            sda_i2c_csv = []
            scl_i2c_csv = []
            with open("csv\\i2c-capture.csv", "r") as csvCapture:
                reader = csv.reader(csvCapture)
                for row in reader:
                    csv_to_list.append(row)
            for i in range(len(csv_to_list)-1):
                time_i2c_csv.append(float(csv_to_list[i][0]))
                scl_i2c_csv.append(float(csv_to_list[i][1]))
                sda_i2c_csv.append(float(csv_to_list[i][2]))
            i2c_clock_offline = Signal(time_i2c_csv, sda_i2c_csv)
            i2c_data_offline = Signal(time_i2c_csv, sda_i2c_csv)
            Signal([], []).plotting_2_ch(i2c_data_offline,
                                         i2c_clock_offline, "SDA", "TIME", "SCL", "TIME")
            # TODO finish this sheizen
            i2c_clock_offline.level_out_signal(3.0)
            print i2c_clock_offline.voltage
            i2c_data_offline.level_out_signal(3.0)
            print i2c_data_offline.voltage

            Signal([], []).plotting_2_ch(i2c_data_offline,
                                         i2c_clock_offline, "SDA", "TIME", "SCL", "TIME")
            i2c_decoded(i2c_data_offline.voltage,
                        i2c_clock_offline.voltage, 100)
    # END I2C------------------------------------------------
    else:
        print "Supported protocols are SPI,CAN,LIN,I2C!"
        sys.exit()
    sys.exit()
