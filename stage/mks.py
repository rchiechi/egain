import time
import threading

XXTS = {0:'Axis connected',
        1:'Motor on',
        2:'Axis in motion',
        3:'reserved',
        4:'origin done',
        5:'reserved',
        6:'reserved',
        7:'reserved',
        8:'Following error',
        9:'Motor fault',
        10:'EOR- reached',
        11:'EOR+ reached',
        12:'ZM reached',
        13:'reserved',
        14:'reserved',
        15:'reserved'}

def asciitobinary(ascii):
    if len(ascii) > 2:
        print(f"Warning: ASCII string {ascii} is longer than two characters!")
    # return ''.join(format(ord(i), '08b') for i in str(ascii, encoding='utf8'))[::-1]
    binary = []
    for i in str(ascii, encoding='utf8'):
        binary.append(format(ord(i), '08b')[::-1])
    return ''.join(binary)

def axisstatustostring(status):
    print('------')
    print(status)
    for i in range(0, len(status)):
        if i > 15:
            print(f"Status {status} string too long!")
            break
        _bool = bool(int(status[i]))
        print(f'{XXTS[i]}: {_bool}')
    print('------')

class CommandThread(threading.Thread):
    '''A Thread object to run stage commands in so it
       doesn't block the main GUI thread.'''

    def __init__(self, parser):
        super().__init__()
        self.parser = parser

    def run(self):
        self.parser.readfiles(self.parser.opts.in_files)

class ESP302(threading.Thread):

    _in_motion = False
    _cmd_queue = []

    def __init__(self, alive, backend):
        super().__init__()
        self.alive = alive
        self._error = False
        self.dev = backend
        self.dev.connect()
        if not self.dev.connected:
            raise IOError('Could not connect backend.')
        for axis in (1,2,3):
            if not self.motorOn(axis):
                self._error = True
                print(f"Error starting up axis {axis} motor!")
            # raise Exception()  # TODO: throw a real exception

    @property
    def error(self):
        return self._error

    @property
    def isMoving(self):
        return self._in_motion

    def run(self):
        while self.alive.isSet():
            if self._cmd_queue:
                _cmd = self._cmd_queue.pop()
                _func = getattr(self, _cmd[0])
                _func(*_cmd[1:])
            time.sleep(0.1)
        for axis in (1,2,3):
            if not self.motorOff(axis):
                self._error = True
                print(f"Error shutting down axis {axis} motor!")

    def _cmd(self, axis, cmd, param=None):
        if param is None:
            _cmdstr = b"%d%s;%dTS\r" % (axis,cmd,axis)
        else:
            _cmdstr = b"%d%s%s;%dTS\r" % (axis,cmd,param,axis)
        self.dev.write(_cmdstr)
        return asciitobinary(self.dev.read())

    def _moveindefinitely(self, axis, direction):
        self._in_motion = True
        _status = self._cmd(axis, b'MF', direction)
        while not bool(int(_status[2])):
            if self._bittobool(_status[8]) or self._bittobool(_status[9]):
                self._in_motion = False
                return False
            time.sleep(1)
        self._in_motion = False
        return True

    def _bittobool(self, bit):
        return bool(int(bit))

    def cleanup(self):
        for axis in (1,2,3):
            if not self.motorOff(axis):
                self._error = True
                print(f"Error shutting down axis {axis} motor!")
                # raise Exception()  # TODO: throw a real exception
        self.dev.disconnect()

    def motorOn(self, axis):
        "Turn on axis motor."
        _status = self._cmd(axis, b'MO')
        axisstatustostring(_status)
        return self._bittobool(_status[1])

    def motorOff(self, axis):
        "Turn off axis motor."
        _status = self._cmd(axis, b'MF')
        axisstatustostring(_status)
        return not self._bittobool(_status[1])

    def stop(self, axis):
        _status = self._cmd(axis, b'ST')
        return self._bittobool(_status[2])

    def moveMax(self, axis):
        self._cmd_queue.append(('_moveindefinitely', axis, b'+'))
        # return self._moveindefinitely(axis, b'+')

    def moveMin(self, axis):
        self._cmd_queue.append(('_moveindefinitely', axis, b'-'))
        # return self._moveindefinitely(axis, b'-')


if __name__ == '__main__':
    from backend import NetHost
    nethost = NetHost()
    stage = ESP302(nethost)
    stage.cleanup()
