# coding: utf-8
"""
Outputing recorded data from oscilloscope to csv.

Used modules in csv_everything.py :
--csv                                1.0
--itertools
--colorama                           0.4.1
"""
import csv
import itertools
import colorama
# for colors in terminal
colorama.init(autoreset=True)


def csv_everything_spi(time, spi_data_to_csv, spi_clock_to_csv):
	"""
	Outputing SPI data to csv.
	--------------------------
	@param spi_data_to -- List of SPI data channel to be recored in csv.
	@param spi_clock_to_csv -- List SPI clock channel to be recorded in csv.
	@param time -- List of time in which interval SPI frame is recoreded.
	--------------------------
	"""
	with open("csv\\spi-capture.csv", "w") as csvCapture:
		csvWriter = csv.writer(csvCapture)
		for val in itertools.izip(time, spi_clock_to_csv, spi_data_to_csv):
				csvWriter.writerow(val)
	print colorama.Fore.MAGENTA + "SPI - CSV output done"


def csv_everything_i2c(time, i2c_data_to_csv, i2c_clock_to_csv):
    """
    Outputing I2C data to csv.
    --------------------------
    @param i2c_data_to_csv -- I2C data channel to be recored in csv.
    @param i2c_clock_to_csv -- I2C clock channel to be recorded in csv.
    @param time -- List of time in which interval I2C frame is recoreded.
    --------------------------
    """
    with open("csv\\i2c-capture.csv", "w") as csvCapture:
	csvWriter = csv.writer(csvCapture)
	for val in itertools.izip(time, i2c_clock_to_csv, i2c_data_to_csv):
	    csvWriter.writerow(val)
    print colorama.Fore.MAGENTA + "SPI - CSV output done"


def csv_everything_can(time, can_data_to_csv):
    """
    Outputing CAN data to csv.
    --------------------------
    @param can_data_to_csv -- CAN data channel to be recored in csv.
    @param time -- List of time in which interval CAN frame is recoreded.
    --------------------------
    """
    with open("csv\\can-capture.csv", "w") as csvCapture:
	csvWriter = csv.writer(csvCapture)
	for val in itertools.izip(time, can_data_to_csv):
	    csvWriter.writerow(val)
    print colorama.Fore.MAGENTA + "CAN - CSV output done"


def csv_everything_lin(time, lin_data_to_csv):
    """
    Outputing LIN data to csv.
    --------------------------
    @param lin_data_to_csv -- LIN data channel to be recored in csv.
    @param time -- List of time in which interval LIN frame is recoreded.
    --------------------------
    """
    with open("csv\\lin-capture.csv", "w") as csvCapture:
	csvWriter = csv.writer(csvCapture)
	for val in itertools.izip(time, lin_data_to_csv):
	    csvWriter.writerow(val)
    print colorama.Fore.MAGENTA + "LIN - CSV output done"
