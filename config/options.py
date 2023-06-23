import os
from datetime import datetime
# from types import SimpleNamespace
from gui.util import parseusersettings

GLOBAL_OPTS = 'global.json'

def createOptions():
    _config = parseusersettings(GLOBAL_OPTS)
    opts = _config.get('opts', {})
    save_path = _config.get('save_path', os.path.expanduser('~'))
    opts['save_path'] = save_path
    dt = datetime.now()
    opts['output_file_name'] = dt.strftime('%Y%m%d_%H%M_')
    return opts
