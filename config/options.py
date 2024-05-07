import os
from datetime import datetime
from pathlib import Path
from gui.util import parseusersettings

GLOBAL_OPTS = 'global.pickle'

def createOptions():
    _config = parseusersettings(GLOBAL_OPTS)
    opts = _config.get('opts', {})
    save_path = Path(_config.get('save_path', os.path.expanduser('~')))
    opts['save_path'] = save_path
    dt = datetime.now()
    opts['output_file_name'] = Path(dt.strftime('%Y%m%d_%H%M_'))
    return opts
