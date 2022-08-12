import time

XXTS=(0:'Axis connected',
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
      15:'reserved')

def asciitobinary(ascii):
    return ''.join(format(ord(i), '08b') for i in ascii)[::-1]

def axisstatustostring(status):
    for i in range(len(status)):
        _bool = bool(status[i])
        print(f'{XXTS[i]}: {_bool}')

class ESP302:

    def __init__(backend):
        self.error = False
        self.dev = backend
        for axis in (1,2,3):
            if not motorOn(axis):
                self.error = True
        if self.error:
            raise Exception()  # TODO: throw a real exception

    def __cmd(self, axis, cmd, param=None):
        if param is None:
            _cmdstr = "%d%s;%dTS\r"%(axis,cmd,axis)
        else:
            _cmdstr = "%d%s%d;%dTS\r"%(axis,cmd,param,axis)
        self.dev.write(_cmdstr)
        return asciitobinary(self.dev.read())
    
    def __moveindefinitely(self, axis, direction):
        _status = asciitobinary(__cmd(axis, 'MF', direction))
        while not bool(int(_status[2]))
            if __bittobool(_status[8]) or __bittobool(_status[9]):
                return False
            time.sleep(1)
        return True
   
   def __bittobool(self, bit):
        return bool(int(bit))
        
    def cleanup(self):
        for axis in (1,2,3):
        if not motorOff(axis):
            self.error = True
        if self.error:
            raise Exception()  # TODO: throw a real exception
   
    def motorOn(self, axis):
        "Turn on axis motor."
        _status = asciitobinary(__cmd(axis, 'MO'))
        return __bittobool(_status[1])

    def motorOff(self, axis):
        "Turn off axis motor."
        _status = asciitobinary(__cmd(axis, 'MF'))
        return __bittobool(_status[1])
    
    def stop(self, axis):
        _status = asciitobinary(__cmd(axis, 'ST'))
        return __bittobool(_status[2])
    
    def moveMax(self, axis):
        return __moveindefinitely(axis, '+')

    def moveMax(self, axis):
        return __moveindefinitely(axis, '-')

    
if __name__ == '__main__':
    from stage.backend import Telnet
    telnet = Telnet()
    stage = ESP302(telnet)
    stage.cleanup()
        