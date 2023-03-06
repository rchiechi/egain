import time
import threading
import random

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



# class CommandThread(threading.Thread):
#     '''A Thread object to run stage commands in so it
#        doesn't block the main GUI thread.'''
# 
#     def __init__(self, parser):
#         super().__init__()
#         self.parser = parser
# 
#     def run(self):
#         self.parser.readfiles(self.parser.opts.in_files)

class Command:

    _res = None
    _done = False

    def __init__(self, _func:str, *args):
        self._id = random.randint(10000,99999)
        self._func = _func
        self._cmd = args

    def complete(self, res=None):
        self._done = True
        self._res = res

    @property
    def id(self):
        return self._id

    @property
    def function(self):
        return self._func

    @property
    def command(self):
        return self._cmd

    @property
    def result(self):
        return self._res

    @property
    def done(self):
        return self._done


class ESP302(threading.Thread):
    '''A Thread object to run stage commands in so it
       doesn't block the main GUI thread.'''
    _in_motion = False
    _cmd_queue = []
    _res_queue = {}
    motion_timeout = 30
    name = 'ESP302'
    AXES = (1,2,3)

    def __init__(self, alive, backend):
        super().__init__()
        self.alive = alive
        self._error = False
        self.dev = backend
        self.dev.connect()
        if not self.dev.connected:
            raise IOError('Could not connect backend.')
        for axis in self.AXES:
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
        print(f'Thread {self.name} started.')
        while self.alive.isSet():
            if self._cmd_queue:
                _cmd = self._cmd_queue.pop()
                _func = getattr(self, _cmd.function)
                print(f'Executing command {_cmd.function}({_cmd.command}).')
                _cmd.complete(_func(*_cmd.command))
                self._res_queue[_cmd.id] = _cmd.res
            time.sleep(0.1)
        for axis in (1, 2, 3):
            if not self.motorOff(axis):
                self._error = True
                print(f"Error shutting down axis {axis} motor!")

    def _cmd(self, axis, cmd, param=None):
        if param is None:
            _cmdstr = b"%d%s;%dTS\r" % (axis, cmd, axis)
        elif isinstance(param, int) or isinstance(param, float):
            _cmdstr = b"%d%s%d;%dTS\r" % (axis, cmd, param, axis)
        else:
            _cmdstr = b"%d%s%s;%dTS\r" % (axis, cmd, param, axis)
        self.dev.write(_cmdstr)
        return asciitobinary(self.dev.read())

    def _getstatus(self, axis):
        self.dev.write(b"%dTS\r" % axis)
        return asciitobinary(self.dev.read())

    def _moveindefinitely(self, axis, direction):
        if self._in_motion:
            return False
        _t = 0
        self._in_motion = True
        self._cmd(axis, b'MF', direction)
        _status = self._getstatus(axis)
        while not bool(int(_status[2])):
            if self._bittobool(_status[8]) or self._bittobool(_status[9]):
                self._in_motion = False
                return False
            if _t > self.motion_timeout:
                print('Timed out executing motion command')
                break
            time.sleep(1)
            _t += 1
            self._waitforcmd()
            _status = self._getstatus(axis)
        self._in_motion = False
        return True

    def _moverelative(self, axis, direction):
        if self._in_motion:
            return False
        _t = 0
        self._in_motion = True
        self._cmd(axis, b'PR', direction)
        _status = self._getstatus(axis)
        while not bool(int(_status[2])):
            if self._bittobool(_status[8]) or self._bittobool(_status[9]):
                self._in_motion = False
                return False
            if _t > self.motion_timeout:
                print('Timed out executing motion command')
                break
            time.sleep(1)
            _t += 1
            self._waitforcmd()
            _status = self._getstatus(axis)
        self._in_motion = False
        return True

    def _setunits(self, axis, unit):
        for axis in self.AXES:
            self._cmd(axis, b'SN', unit)

    def _getunits(self):
        units = []
        for axis in self.AXES:
            self.dev.write(b'%dSN?\r' % axis)
            units.append(int(self.dev.read()))
        return units

    def _getposition(self):
        self.dev.write(b'TP\r')
        _x, _y, _z = self.dev.read().split(b',')
        return (float(_x), float(_y), float(_z))

    def _bittobool(self, bit):
        return bool(int(bit))

    def _waitformotion(self):
        _t = 0
        while self._in_motion:
            time.sleep(0.1)
            _t += 10
            if _t > self.motion_timeout:
                break

    def waitForStage(self):
        self._waitformotion()

    def getresult(self, _id, block=False):
        if block:
            while _id not in self._res_queue:
                time.sleep(0.1)
            return self._res_queue[_id]
        else:
            return self._res_queue.get(_id, False)

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
        _cmd = Command('_moveindefinitely', axis, b'+')
        self._cmd_queue.append(_cmd)
        return _cmd.id
        # self._cmd_queue.append(('_moveindefinitely', axis, b'+'))
        # return self._moveindefinitely(axis, b'+')

    def moveMin(self, axis):
        _cmd = Command('_moveindefinitely', axis, b'-')
        self._cmd_queue.append(_cmd)
        return _cmd.id
        # self._cmd_queue.append(('_moveindefinitely', axis, b'-'))
        # return self._moveindefinitely(axis, b'-')

    def relativeMove(self, axis, distance):
        _cmd = Command('_moverelative', axis, distance)
        self._cmd_queue.append(_cmd)
        return _cmd.id
        # self._cmd_queue.append(('_moverelative', axis, distance))

    def setUnits(self, unit):
        _cmd = Command('_setunits', unit)
        self._cmd_queue.append(_cmd)
        return _cmd.id
        # self._cmd_queue.append(('_setunits', axis, unit))

    def getUnits(self):
        _cmd = Command('_getunits')
        self._cmd_queue.append(_cmd)
        return self.getresult(_cmd.id, True)
        # self.waitForStage()
        # units = []
        # for axis in self.AXES:
        #     self.dev.write(b'%dSN?\r' % axis)
        #     units.append(int(self.dev.read()))
        # return units

    def getPosition(self):
        _cmd = Command('_getposition')
        self._cmd_queue.append(_cmd)
        return self.getresult(_cmd.id, True)
        # self.waitForStage()
        # self.dev.write(b'TP\r')
        # _x, _y, _z = self.dev.read().split(b',')
        # return (float(_x), float(_y), float(_z))


if __name__ == '__main__':
    from backend import NetHost
    nethost = NetHost()
    stage = ESP302(nethost)
    stage.cleanup()
