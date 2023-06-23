import os
import subprocess
import socket
import json

def ping(host):
    if host is None:
        return False
    if not _validateip(host):
        return False
    if host is not None:
        _ping = subprocess.run(['which','ping'], capture_output=True)
        p = subprocess.run([_ping.stdout.decode('utf-8').strip(), '-q', '-c1', '-W1', '-n', host], stdout=subprocess.PIPE)
        if p.returncode == 0:
            return True
    return False

def _validateip(addr):
    try:
        socket.inet_aton(addr)
        # legal
        return True
    except socket.error:
        # Not legal
        return False

def parseusersettings(config_file, payload={}):
    if not os.path.exists(os.path.split(config_file)[0]):
        os.makedirs(os.path.split(config_file)[0])
    try:
        if not payload:
            with open(config_file) as fh:
                return json.load(fh)
        else:
            with open(config_file, 'wt') as fh:
                json.dump(payload, fh)
    except json.decoder.JSONDecodeError:
        print("Error parsing user settings.")
    except IOError:
        print(f"{config_file} not found.")
    return {}