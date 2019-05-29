# coding: utf-8
# -------------------------------------------------------------------------------
#  As the name says, outputing recorded data to csv
#  TODO : outputing decoded data 
# -------------------------------------------------------------------------------
import csv
import itertools


def csv_everything_spi(data_final_spi, clock_final_spi, time):
    with open("spi-capture.csv", "w") as csvCapture:
        csvWriter = csv.writer(csvCapture)
        for val in itertools.izip(time, clock_final_spi, data_final_spi):
            csvWriter.writerow(val)
    print "SPI - CSV output done"


def csv_everything_i2c(data_final_i2c, clock_final_i2c, time):
    with open("i2c-capture.csv", "w") as csvCapture:
        csvWriter = csv.writer(csvCapture)
        for val in itertools.izip(time, clock_final_i2c, data_final_i2c):
            csvWriter.writerow(val)
    print "SPI - CSV output done"


def csv_everything_can(data_final_can, time):
    with open("can-capture.csv", "w") as csvCapture:
        csvWriter = csv.writer(csvCapture)
        for val in itertools.izip(time, data_final_can):
            csvWriter.writerow(val)
    print "CAN - CSV output done"


def csv_everything_lin(data_final_lin, time):
    with open("lin-capture.csv", "w") as csvCapture:
        csvWriter = csv.writer(csvCapture)
        for val in itertools.izip(time, data_final_lin):
            csvWriter.writerow(val)
print "LIN - CSV output done"