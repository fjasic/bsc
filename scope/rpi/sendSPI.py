import spidev
import time
import datetime

outputFile = "data"

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=7629
for x in range (0,1000):
        to_send = [0xff, 0xff, 0xff]
        spi.xfer(to_send)
spi.close()
