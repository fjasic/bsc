# coding: utf-8
import visa
import numpy as np
from struct import unpack
import pylab
import sys
from ssh_spi import ssh_call_spi
from lin_decoding import lin_decoded
from spi_decoding import spi_decoded
# from csv_output import *
import csv
import warnings
import os
import colorama
# for colors in terminal
colorama.init(autoreset=True)


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
    volts = (ADC_wave - yoff) * ymult + yzero
    time = np.arange(0, xincr * len(volts), xincr)
    return volts, time


def set_channel(scope, channel):
    scope.write('DATA:SOU CH' + str(channel))


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print "USAGE : readout.py protocol[CAN,LIN,SPI,I2C] protocol_version(only for LIN)[-c for classic -e for enhanced]"
        sys.exit()
    # YOU CAN SEE YOUR INSTRUMENT ID IN OpenChoiceDesktop APPLICATION
    instrument_id = 'USB0::0X0699::0x0401::C021046::INSTR'
    warnings.simplefilter(action='ignore', category=FutureWarning)
    # START--------------------------------------------------
    # -------------------------------------------------------
    # -------------------------------------------------------
    # SPI----------------------------------------------------
    if sys.argv[1] == "SPI":
        # GENERISANJE SPI SIGNALA
        # ssh_call_spi()
        ##########################
        ##########################
        # OBRADA SPI SIGNALA
        csv_to_list = []
        time = []
        clock_voltage = []
        data_voltage = []
        with open("csv\\spi-capture.csv", "r") as csvCapture:
            reader = csv.reader(csvCapture)
            for row in reader:
                csv_to_list.append(row)
        for i in range(len(csv_to_list)-1):
            time.append(float(csv_to_list[i][0]))
            clock_voltage.append(float(csv_to_list[i][1]))
            data_voltage.append(float(csv_to_list[i][2]))
        for i in range(len(time)):
            if clock_voltage[i] > 3.0:
                clock_voltage[i] = 1
            else:
                clock_voltage[i] = 0
            if data_voltage[i] > 3.0:
                data_voltage[i] = 1
            else:
                data_voltage[i] = 0
        pylab.subplot(2, 1, 1)
        pylab.plot(time, clock_voltage)
        pylab.subplot(2, 1, 2)
        pylab.plot(time, data_voltage)
        pylab.show()
        sample_period = 13
        data = spi_decoded(clock_voltage, data_voltage, time, sample_period)
        print "data: " + str(data)
    # END SPI------------------------------------------------

    # CAN----------------------------------------------------
    elif sys.argv[1] == "CAN":
        # serial_call_can()
        pass
    # END CAN------------------------------------------------

    # LIN----------------------------------------------------
    elif sys.argv[1] == "LIN":
        # GENERISANJE LIN SIGNALA
        # serial_call_lin()
        #########################
        #########################
        # OBRADA LIN SIGNALA
        time_total = []
        voltage_total = []
        length_of_dir = os.listdir("E:\\scope")
        number_of_files = 0
        while number_of_files < len(length_of_dir):
            time = []
            voltage = []
            csv_to_list = []
            file_to_open = "E:\\scope\\All_%s.csv" % (str(number_of_files+1))
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
        # ssh_call_i2c()
        i2c_ch_data = sys.argv[2]
        i2c_ch_clock = sys.argv[3]
        if int(i2c_ch_data) > 4 or int(i2c_ch_clock) > 4:
            print "Works only for oscilloscopes with 4 channels maximum"
            sys.exit()
        print "I2C - PLOT done"
        print "I2C - PNG output done"
        print "Exit figure to end program..."
    # END I2C------------------------------------------------
    else:
        print "Supported protocols are SPI,CAN,LIN,I2C!"
        sys.exit()
    sys.exit()
