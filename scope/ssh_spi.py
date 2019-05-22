import paramiko


def Connect(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    if client is None:
        return None
    else:
        return client


def ssh_call_spi():
    client = Connect("169.254.2.187", port=22, user="pi", password="pi")
    client.exec_command("python SPI-Test/readSpi.py\n")
    client.close()
