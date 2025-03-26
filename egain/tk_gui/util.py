import os
import sys
import logging
import subprocess
import socket
import pickle
from pathlib import Path
from appdirs import user_config_dir

logger = logging.getLogger(__package__+'.util')

def ping(host):
    if host is None:
        return False
    if not validateip(host):
        return False
    _which = 'which' if not sys.platform.startswith('win32') else 'where'
    if host is not None:
        _ping = subprocess.run([_which,'ping'], capture_output=True)
        p = subprocess.run([_ping.stdout.decode('utf-8').strip(), '-q', '-c1', '-W1', '-n', host], stdout=subprocess.PIPE)
        if p.returncode == 0:
            return True
    return False

def validateip(addr):
    try:
        socket.inet_aton(addr)
        # legal
        return True
    except socket.error:
        # Not legal
        return False

def parseusersettings(_file, payload={}):
    config_file = Path(user_config_dir('egain', 'rcclab'), os.path.basename(_file))
    if not os.path.exists(os.path.split(config_file)[0]):
        os.makedirs(os.path.split(config_file)[0])
    try:
        if not payload:
            with config_file.open('rb') as fh:
                return pickle.load(fh)
        else:
            with config_file.open('wb') as fh:
                pickle.dump(payload, fh)
    except pickle.UnpicklingError:
        logger.warning("Error parsing user settings.")
        config_file.unlink(missing_ok=True)
    except pickle.PicklingError:
        logger.warning("Error saving user settings.")
        config_file.unlink(missing_ok=True)
    except IOError:
        logger.debug(f"{config_file} not found.")
    return {}