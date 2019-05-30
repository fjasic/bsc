# coding: utf-8
# -------------------------------------------------------------------------------
#  Automating oscilloscope for continious recording and decoding of CAN, LIN,
#  I2C,SPI protocols

# python                             2.7.15
# PyVISA                             1.9.1
# matplotlib                         2.2.4
# colorama                           0.4.1

# -------------------------------------------------------------------------------
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
from serial_can import serial_call_can
from lin_decoding import lin_decoded
from spi_decoding import spi_decoded
from can_decoding import can_decoded
from csv_everything import csv_everything_can
from kmp import KnuthMorrisPratt
# for colors in terminal
colorama.init(autoreset=True)
# TODO:automatic setting of controls on oscilloscope and i2c decoding, doxygen


def main(instrument_id, channel_num):
    volts_final = []
    time_final = []
    try:
        scope = visa.ResourceManager().open_resource(instrument_id)
        set_channel(scope, str(channel_num))
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
            for i in range(len(volts)):
                volts_final.append(volts[i])
            for i in range(len(time)):
                time[i] = float(time[i]) + 1.0 * (loop-1)
                time_final.append(time[i])
            while '1' in scope.ask("BUSY?"):
                pass
    except KeyboardInterrupt:
        return volts, time


def set_channel(scope, channel):
    scope.write('DATA:SOU CH' + str(channel))


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print """USAGE : readout.py protocol[CAN,LIN,SPI,I2C] protocol_version
        (only for LIN)[-c for classic -e for enhanced]"""
        sys.exit()
    # YOU CAN SEE YOUR INSTRUMENT ID IN OpenChoiceDesktop APPLICATION
    instrument_id = 'USB0::0X0699::0x0401::C021046::INSTR'
    # ignoring FutureWarning
    warnings.simplefilter(action='ignore', category=FutureWarning)
    print colorama.Fore.YELLOW + "press Ctrl+C to stop measurment"
    # START--------------------------------------------------

    # SPI----------------------------------------------------
    if sys.argv[1] == "SPI":
        # GENERATING SPI SIGNAL
        # ssh_call_spi()
        # READOUT OF RECORDED SPI SIGNAL
        csv_to_list = []
        time = []
        clock_voltage = []
        data_voltage = []
        # change sample period, look on osclilloscope
        sample_period = 13
        with open("csv\\spi-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        for i in range(len(csv_to_list)-1):
            time.append(float(csv_to_list[i][0]))
            clock_voltage.append(float(csv_to_list[i][1]))
            data_voltage.append(float(csv_to_list[i][2]))
        # leveling voltage at 1.0 and 0 depending on raw voltage levels
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
        # decoding spi and returning decoded data
        data = spi_decoded(clock_voltage, data_voltage, time, sample_period)
        print "data: " + str(data)
    # END SPI------------------------------------------------

    # CAN----------------------------------------------------
    elif sys.argv[1] == "CAN":
        # GENERATING CAN SIGNAL
        # serial_call_can()
        # READOUT OF RECORDED CAN SIGNAL
        csv_to_list = []
        time_to_decode = []
        data_voltage_high_to_decode = []
        data_voltage_low = []
        sample_period = 100
        print "if " + colorama.Fore.RED + "red " + colorama.Fore.WHITE + "color shows up,data is not correct"
        print "else " +colorama.Fore.GREEN + "green " + colorama.Fore.WHITE + "it's all good!"
        """getting can frames, only from channel 1 (CAN_H),
        because channel 2 (CAN_L) is mirror of first channel"""
        data_final_can, time_can = main(instrument_id, "1")

        # leveling voltage at 1.0 and 0 depending on raw voltage levels
        for i in range(len(data_final_can)):
            if data_final_can[i] > 3.0:
                data_final_can[i] = 1
            else:
                data_final_can[i] = 0
        plt.xlabel("time")
        plt.ylabel("voltage_high")
        plt.plot(time_can, data_final_can)
        plt.show()
        print "\n"
        csv_everything_can(data_final_can, time_can)
        with open("can-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        csv_to_list_final = csv_to_list
        for i in range(len(csv_to_list_final)-1):
            time_to_decode.append(float(csv_to_list_final[i][0]))
            data_voltage_high_to_decode.append(float(csv_to_list_final[i][1]))
        inter_frame = []
        inter_frame_start = []
        for i in range(31*10):
            inter_frame.append(0.0)
        for s in KnuthMorrisPratt(data_voltage_high_to_decode, inter_frame):
            inter_frame_start.append(s)
        if inter_frame_start == []:
            inter_frame = []
            for i in range(30*10):
                inter_frame.append(0.0)
            for s in KnuthMorrisPratt(data_voltage_high_to_decode, inter_frame):
                inter_frame_start.append(s)
            if inter_frame_start == []:
                inter_frame = []
                for i in range(29*10):
                    inter_frame.append(0.0)
                for s in KnuthMorrisPratt(data_voltage_high_to_decode, inter_frame):
                    inter_frame_start.append(s)
                if inter_frame_start == []:
                    inter_frame = []
                    for i in range(28*10):
                        inter_frame.append(0.0)
                    for s in KnuthMorrisPratt(data_voltage_high_to_decode, inter_frame):
                        inter_frame_start.append(s)
                    if inter_frame_start == []:
                        inter_frame = []
                        for i in range(27*10):
                            inter_frame.append(0.0)
                        for s in KnuthMorrisPratt(data_voltage_high_to_decode, inter_frame):
                            inter_frame_start.append(s)
                        plt.plot(time_to_decode[inter_frame_start[0]+270:inter_frame_start[1]],
                                 data_voltage_high_to_decode[inter_frame_start[0]+270:inter_frame_start[1]])
                        plt.show()
                        for i in range(len(inter_frame_start)-1):
                            can_decoded(data_voltage_high_to_decode[inter_frame_start[i]+270:inter_frame_start[i+1]],
                                        time_to_decode[inter_frame_start[i]+270:inter_frame_start[i+1]], 10)
                    else:
                        plt.plot(time_to_decode[inter_frame_start[0]+280:inter_frame_start[1]],
                                 data_voltage_high_to_decode[inter_frame_start[0]+280:inter_frame_start[1]])
                        plt.show()
                        for i in range(len(inter_frame_start)-1):

                            can_decoded(data_voltage_high_to_decode[inter_frame_start[i]+280:inter_frame_start[i+1]],
                                        time_to_decode[inter_frame_start[i]+280:inter_frame_start[i+1]], 10)
                else:
                    plt.plot(time_to_decode[inter_frame_start[0]+290:inter_frame_start[1]],
                             data_voltage_high_to_decode[inter_frame_start[0]+290:inter_frame_start[1]])
                    plt.show()
                    for i in range(len(inter_frame_start)-1):
                        can_decoded(data_voltage_high_to_decode[inter_frame_start[i]+290:inter_frame_start[i+1]],
                                    time_to_decode[inter_frame_start[i]+290:inter_frame_start[i+1]], 10)
            else:
                plt.plot(time_to_decode[inter_frame_start[0]+300:inter_frame_start[1]],
                         data_voltage_high_to_decode[inter_frame_start[0]+300:inter_frame_start[1]])
                plt.show()
                for i in range(len(inter_frame_start)-1):
                    can_decoded(data_voltage_high_to_decode[inter_frame_start[i]+300:inter_frame_start[i+1]],
                                time_to_decode[inter_frame_start[i]+300:inter_frame_start[i+1]], 10)
        else:
            plt.plot(time_to_decode[inter_frame_start[0]+310:inter_frame_start[1]],
                     data_voltage_high_to_decode[inter_frame_start[0]+310:inter_frame_start[1]])
            plt.show()
            for i in range(len(inter_frame_start)-1):
                can_decoded(data_voltage_high_to_decode[inter_frame_start[i]+310:inter_frame_start[i+1]],
                            time_to_decode[inter_frame_start[i]+310:inter_frame_start[i+1]], 10)

    # END CAN------------------------------------------------

    # LIN----------------------------------------------------
    elif sys.argv[1] == "LIN":
        # GENERATING LIN SIGNAL
        # serial_call_lin()
        # READOUT OF RECORDED LIN SIGNAL
        time_total = []
        voltage_total = []
        length_of_dir = os.listdir("F:\\scope")
        number_of_files = 0
        while number_of_files < len(length_of_dir):
            time = []
            voltage = []
            csv_to_list = []
            file_to_open = "F:\\scope\\All_%s.csv" % (str(number_of_files+1))
            print file_to_open,
            with open(file_to_open, "r") as csvCapture:
                reader = csv.reader(csvCapture)
                for row in reader:
                    csv_to_list.append(row)
            csv_to_list_final = csv_to_list[16:]
            for i in range(len(csv_to_list_final)-1):
                time.append(float(csv_to_list_final[i][0]))
                voltage.append(float(csv_to_list_final[i][1]))

            time_total += time
            voltage_total += voltage
            index_start_lin = 0
            for i in range(len(voltage)):
                if voltage[i] < 10.0:
                    index_start_lin = i
                    break
            voltage = voltage[index_start_lin:]
            time = time[index_start_lin:]
            for i in range(len(voltage)):
                if voltage[i] <= 2.0:
                    voltage[i] = 0
                else:
                    voltage[i] = 1
            voltage[0] = 0
            sample_interval = 50
            lin_id, lin_parity_bits, lin_data, lin_checksum = lin_decoded(
                voltage, time, sample_interval)
            output = "ID: " + str(lin_id) + "||PARITY BITS: " + \
                str(lin_parity_bits) + "||DATA: " + str(lin_data) + \
                "||CHECKSUM: " + str(lin_checksum)
            # CHECKSUM AND PARITY BITS
            checksum = 0
            lin_ver = sys.argv[2]
            data = [int(c) for c in lin_data]
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

            hex_int_checksum = int("0x" + str(checksum), 16)
            # inversion
            new_int_checksum = 0xff - hex_int_checksum
            final_checksum = int(hex(new_int_checksum)[-2:])
            if lin_checksum == final_checksum and final_parity == lin_parity_bits:
                print colorama.Fore.GREEN + output
                number_of_files += 1
            elif lin_checksum != final_checksum:
                print colorama.Fore.RED + output + "[CHECKSUM ERROR]"
                number_of_files += 1
            elif final_parity != lin_parity_bits:
                print colorama.Fore.RED + output + "[PARITY ERROR]"
                number_of_files += 1
            else:
                print colorama.Fore.RED + output + \
                    "[PARITY AND CHECKSUM ERROR]"
                number_of_files += 1
    # END LIN------------------------------------------------

    # I2C----------------------------------------------------
    elif sys.argv[1] == "I2C":
        # GENERATING I2C SIGNAL
        # ssh_call_i2c()
        # READOUT OF RECORDED I2C SIGNAL
        print "I2C - PLOT done"
        print "I2C - PNG output done"
        print "Exit figure to end program..."
    # END I2C------------------------------------------------
    else:
        print "Supported protocols are SPI,CAN,LIN,I2C!"
        sys.exit()
    sys.exit()
