# coding: utf-8
import paramiko
"""
Connects to Raspberry Pi and runs a scripts which sends I2C frames for measurment.

Used in ssh_i2c.py :
--paramiko                           2.4.2
"""


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


def ssh_call_i2c():
    """
    Runs the script for sending I2C frames.
    """
    client = Connect("169.254.2.187", port=22, user="pi", password="pi")
    client.exec_command("python I2C-Test/sendI2C.py\n")
    client.close()
