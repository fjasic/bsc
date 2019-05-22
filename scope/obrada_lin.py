import csv
import re
from collections import Counter


regexTime = re.compile(r".*,")
regexVoltage = re.compile(r",.*")
time = []
voltage = []


def most_common(lst):
    return max(set(lst), key=lst.count)

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

uzorkovanje = 50
results = []
sync_break = voltage_for_realz[0:14*uzorkovanje]
sync_field = voltage_for_realz[14*uzorkovanje:23*uzorkovanje]
sync_break_str = ""
sync_field_str = ""

for i in range(len(sync_break)/uzorkovanje-1):
    sync_break_str += str(most_common(sync_break[i*50:i*50+50]))
results.append(sync_break_str)
print "sync break: " + sync_break_str
for i in range(len(sync_field)/uzorkovanje-1):
    sync_field_str += str(most_common(sync_field[i*50:i*50+50]))
results.append(sync_field_str)
print "sync field: " + sync_field_str
for x in range(8):
    str3 = ""
    for i in range(8):
        str3 += str(most_common(voltage_for_realz[(25+(x*10))*uzorkovanje:(33+(x*10))*uzorkovanje][i*50:i*50+50]))
        # print str3 
        if i == 7:
            results.append("{0:0>2X}".format(int(str3[::-1], 2)))
print results

