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
    with open("lin-capture.csv", "r") as csvCapture:
        string = csvCapture.read()
    time = regexTime.findall(string)
    voltage = regexVoltage.findall(string)

    time_for_realz = []
    voltage_for_realz = []
    for i in range(len(time)):
        time_for_realz.append(float(time[i][:-1]))
    for i in range(len(time)):
        voltage_for_realz.append(int(float(voltage[i][1:])))
    # uzorkovanje menjati po potrebi
    uzorkovanje = 50
    decoded_lin = []
    pylab.plot(time_for_realz, voltage_for_realz)
    pylab.show()
    for i in range(len(voltage_for_realz) / uzorkovanje):
        decoded_lin.append(
            int(most_common(voltage_for_realz[i * uzorkovanje:i * uzorkovanje + uzorkovanje])))
    # results = []
    sync_break = decoded_lin[0:13]
    print "sync break is :" + str(sync_break)
    sync_field = decoded_lin[15:22]
    sync_field_to_hex = ""
    for i in range(len(sync_field)):
        sync_field_to_hex += str(sync_field[i])
    print "sync field is :" + str(sync_field)
    sync_field_hex = "{0:0>2X}".format(int(sync_field_to_hex, 2))
    print "sync field in hex representation: " + str(sync_field_hex)
    rest_of_lin = decoded_lin[25:len(decoded_lin)]
    for x in range(8):
        print "{0:0>2X}".format(
            int("".join(map(str, decoded_lin[(25 + (x * 10)):(33 + (x * 10))][::-1])), 2))
        print x


if __name__ == "__main__":
    main()