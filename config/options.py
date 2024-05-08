import os
import argparse
from datetime import datetime
from pathlib import Path
from gui.util import parseusersettings

GLOBAL_OPTS = 'global.pickle'

def createOptions():
    _config = parseusersettings(GLOBAL_OPTS)
    opts = _config.get('opts', {})
    opts['save_path'] = _config.get('save_path', os.path.expanduser('~'))
    opts['isafm'] = _config.get('isafm', 0)
    dt = datetime.now()
    opts['output_file_name'] = Path(dt.strftime('%Y%m%d_%H%M_'))
    return opts

def parsecliopts():
    '''Parse command line arguments and config file and return opts'''

    desc = '''Software for measuring tunneling junctions with EGaIn
              or CP-AFM and a Keithley SMU.'''
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse
                                     .ArgumentDefaultsHelpFormatter)

    parser.add_argument('--quiet', action="store_true",
                        default=False,
                        help="Silence the SMU.")

    parser.add_argument('--debug', action="store_true",
                        default=False,
                        help="Turn on debug logging.")

    opts = parser.parse_args()
    return opts
