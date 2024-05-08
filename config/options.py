import os
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
