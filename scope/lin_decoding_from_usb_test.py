import csv
import re
from collections import Counter
import pylab

regexTime = re.compile(r".*,")
regexVoltage = re.compile(r",.*")
time = []
voltage = []


def most_common(lst):
    return max(set(lst), key=lst.count)


def main():
    flag_finished = 0
    time_for_realz = []
    voltage_for_realz = []
    with open("All_3.csv", "r") as csvCapture:
        time_for_realz = (list(filter(regexTime.match, csvCapture[16:])))
    time = regexTime.findall(string)
    voltage = filter(regexVoltage.search, string)
    time_for_realz = []
    voltage_for_realz = []
    # for i in range(len(time)):
    #     time_for_realz.append(float(time[i][:-1]))
    # for i in range(len(voltage)):
    #     if voltage[i] == ",":
    #         pass
    #     else:
    #         voltage_for_realz.append(int(float(voltage[i][1:])))
    # print time_for_realz
    # uzorkovanje menjati po potrebi
    # uzorkovanje = 50
    # decoded_lin = []
    # for i in range(len(voltage_for_realz) / uzorkovanje):
    #     decoded_lin.append(
    #         int(most_common(voltage_for_realz[i * uzorkovanje:i * uzorkovanje + uzorkovanje])))
    # # results = []
    # sync_break = decoded_lin[0:13]
    # print "sync break is:" + str(sync_break)
    # sync_field = decoded_lin[15:22]
    # sync_field_to_hex = ""
    # for i in range(len(sync_field)):
    #     sync_field_to_hex += str(sync_field[i])
    # sync_field_hex = "{0:0>2X}".format(int(sync_field_to_hex, 2))
    # print "sync field in hex representation: " + str(sync_field_hex)
    # rest_of_lin = decoded_lin[25:len(decoded_lin)]
    # id_field = ""
    # parity_bits = ""
    # data_field = []
    # # length = 1(id_field) + [1-8](data) + 1(checksum)
    # length = 3
    # for x in range(length):
    #     if x == 0:
    #         id_field = "{0:0>2X}".format(
    #             int("".join(map(str, decoded_lin[(25 + (x * 10)):(33 + (x * 10))][::-1])), 2))
    #         parity_bits = "{0:b}".format(
    #             int("".join(map(str, decoded_lin[(25 + (x * 10)):(33 + (x * 10))][::-1])), 2))[0:2]
    #     else:
    #         data_field.append("{0:0>2X}".format(
    #             int("".join(map(str, decoded_lin[(25 + (x * 10)):(33 + (x * 10))][::-1])), 2)))
    # # print "parity bits are: p1-->" + id_field[0] + " p2-->" + id_field[1]
    # print "id field: " + id_field
    # print "parity_bits: p1-->" + parity_bits[0] + " p2-->" + parity_bits[1]
    # print "data_field: " + str(data_field[:-1])
    # print "checksum: " + str(data_field[-1])
if __name__ == "__main__":
    main()