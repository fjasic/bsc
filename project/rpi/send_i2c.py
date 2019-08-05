# coding: utf-8
"""
Generating I2C signal,10000 times.

Used modules in sendI2C.py :
--smbus
"""
import smbus

bus = smbus.SMBus(1)

for x in range(0, 10000):
    bus.write_byte(0x53, 0xff)
