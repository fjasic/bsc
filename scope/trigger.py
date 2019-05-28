# -------------------------------------------------------------------------------
#  Save All waveforms to USB every time scope triggers

# python        2.7         (http://www.python.org/)
# pyvisa        1.4         (http://pyvisa.sourceforge.net/)
# -------------------------------------------------------------------------------
import visa
import time
import datetime
# Connect to the instrument
scope = visa.ResourceManager().open_resource("USB0::0X0699::0x0401::C021046::INSTR")

# Configure how files are saved, setting resolution to reduced will be faster, but
# you get less actual data
scope.write("SAVE:WAVEFORM:FILEFORMAT SPREADSHEET")
scope.write("SAVE:WAVEFORM:SPREADSHEET:RESOLUTION FULL")

# Create directory where files will be saved
scope.write("FILESYSTEM:MAKEDIR \"E:/scope\"")

# Start single sequence acquisition
scope.write("ACQ:STOPA SEQ")
loop = 0

while True:
    # increment the loop counter
    loop += 1

    print ('On Loop %s' % loop)
    # Arm trigger, then loop until scope has triggered
    scope.write("ACQ:STATE ON")
    while '1' in scope.ask("ACQ:STATE?"):
        time.sleep(0.1)
    # save all waveforms, then wait for the waveforms to be written
    scope.write("SAVE:WAVEFORM ALL, \"E:/scope/DAY3_from_platform_CAN_%s.csv\"" % loop)
    scope.write("RECALL:WAVEFORM 1.csv", "C:/scope")
    while '1' in scope.ask("BUSY?"):
        time.sleep(0.1)
