import socket

class NetHost:

    IP_ADDRESS = '192.168.254.254'
    PORT = '5001'
    _connected = False
    _message_queue = []

    @property
    def connected(self):
        return self._connected

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.IP_ADDRESS, int(self.PORT)))
        self._connected = True

    def disconnect(self):
        self.conn.shutdown(socket.SHUT_RDWR)
        self._connected = False

    def write(self, cmd):
        if not self._connected:
            raise IOError('Connection to stage is closed.')
        print(f'Sending {cmd}')
        self.conn.sendall(cmd)
        self._message_queue.append(self.conn.recv(1024).strip())
        print(f"Received:{self._message_queue[-1]}")

    def read(self):
        if self._message_queue:
            return self._message_queue.pop()
        else:
            return ''


if __name__ == '__main__':
    tel = NetHost()
    tel.write('1TS\r')
    print(tel.read())
