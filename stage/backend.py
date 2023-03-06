import socket

IP_ADDRESS = '192.168.42.2'
PORT = '5001'


class GenericBackEnd:

    _connected = False
    _message_queue = []
    address = IP_ADDRESS
    port = PORT

    @property
    def connected(self):
        return self._connected

    @property
    def getaddress(self):
        return (self.address, self.port)

    def initialize(self, **kwargs):
        self.address = kwargs.get('address', IP_ADDRESS)
        self.port = kwargs.get('port', PORT)

    def connect(self):
        self._connected = True

    def disconnect(self):
        self._connected = False

    def send(self, cmd):
        return

    def receive(self):
        return b"P@"

    def write(self, cmd):
        if not self._connected:
            raise IOError('Connection to stage is closed.')
        print(f'Sending {cmd}')
        self.send(cmd)
        self._message_queue.append(self.receive())
        # print(f"Received:{self._message_queue[-1]}")

    def read(self):
        if self._message_queue:
            return self._message_queue.pop()
        else:
            return ''

class NetHost(GenericBackEnd):

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.address, int(self.port)))
        self.conn.settimeout(10)
        #self.conn.setblocking(False)
        self._connected = True

    def disconnect(self):
        self.conn.shutdown(socket.SHUT_RDWR)
        self._connected = False

    def send(self, cmd):
        self.conn.sendall(cmd)

    def receive(self):
        return self.conn.recv(1024).strip()


if __name__ == '__main__':
    tel = NetHost()
    tel.write('1TS\r')
    print(tel.read())
