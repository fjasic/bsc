import csv 
import re
csvFajl = open("can-f1ca-ch2-l.csv", "r")
csvFajlFinal = open("can-f1ca-ch2-l-final.csv", "wb")
timeRegex = re.compile(r".*,")
voltageRegex = re.compile(r",.*")
textCsv = ""
for row in csvFajl:
    textCsv += str(row)

timeColumn = timeRegex.findall(textCsv)
timeFinal = []
for value in timeColumn:
    timeFinal.append(value[:-1])

voltageColumn = voltageRegex.findall(textCsv)
voltageFinal = []
for value in voltageColumn:
    voltageFinal.append(value[1:4])
csvFajl.close()
wtr = csv.writer(csvFajlFinal, delimiter=",", quoting=csv.QUOTE_ALL)
values = [timeFinal, voltageFinal]
for column in itertools.izip(*values):
    print column[0],
    print column[1]

csvFajlFinal.close()