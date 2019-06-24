# coding: utf-8
"""
Connects to Raspberry Pi and runs a scripts which sends SPI frames for measurment.

Used in ssh_spi.py :
--paramiko                           2.4.2
"""
import paramiko

def Connect(server, port, user, password):
    """
    Connects to device via SSH.
    ---------------------------
    @param server -- IP adress of device.
    @param port -- On which port is device.
    @param user -- Username of device.
    @param password -- Password of device.
    ---------------------------
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    if client is None:
        return None
    else:
        return client


def ssh_call_spi():
    """
    Runs the script for sending SPI frames.
    """
    client = Connect("192.168.137.187", port=22, user="pi", password="pi")
    client.exec_command("python SPI-Test/sendSPI.py\n")
    client.close()
