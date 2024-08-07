AUTH_KEY = b'ZGUwNzkyNTFmM2VhNjRhMTdjNDI3YWY5'
PELTIER_PORT = 6042
THERMO_PORT = 6023
VOLTA_PORT = 6024
TERMINATOR = b';'
COMMAND_READ = 'READ'
COMMAND_STAT = 'STAT'
COMMAND_SEND = 'SEND'
COMMAND_RUN = 'RUN'
COMMAND_STOP = 'STOP'
STAT_OK = 'OK'
STAT_ERROR = 'ERROR'

# Commands
INIT = b'INIT'  # null
POLL = b'POLL'  # null
LEFTON = b'LEFTON'  # null
LEFTOFF = b'LEFTOFF'  # null
RIGHTON = b'RIGHTON'  # null
RIGHTOFF = b'RIGHTOFF'  # null
SETLEFTTEMP = b'SETLEFTTEMP'  # float
SETRIGHTTEMP = b'SETRIGHTTEMP'  # float
LEFTHEAT = b'LEFTHEAT'  # null
LEFTCOOL = b'LEFTCOOL'  # null
RIGHTHEAT = b'RIGHTHEAT'  # null
RIGHTCOOL = b'RIGHTCOOL'  # null
SHOWSTATUS = b'SHOWSTATUS'  # null
# Responses
INITIALIZED = 'INITIALIZED'  # bool
LEFTTARGET = 'LEFTTARGET'  # float
RIGHTTARGET = 'RIGHTTARGET'  # float
PELTIERON = 'PELTIERON'  # bool
LEFTPOWER = 'LEFTPOWER'  # float
RIGHTPOWER = 'RIGHTPOWER'  # float
HEAT = 'HEAT'  # const
COOL = 'COOL'  # const
LEFT = 'LEFT'  # const
RIGHT = 'RIGHT'  # const
LEFTFLOW = 'LEFTFLOW'  # HEAT/COOL
RIGHTFLOW = 'RIGHTFLOW'  # HEAT/COOL
