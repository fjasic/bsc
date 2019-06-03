# coding: utf-8
"""
Generating I2C signal,10000 times.

Used modules in sendI2C.py :
--i2cdev                                1.2.4
"""
from i2cdev import I2C

device, bus = 0x53, 1
i2c = I2C(device, bus)
value = i2c.read(1)

for i in range(10000):
    i2c.write(b"1111")
