import socket

class Telnet:

    IP_ADDRESS = '192.168.254.254'
    PORT = '5001'
    message_queue = []

    def __init__(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.IP_ADDRESS, int(self.PORT)))

    # def write(self, cmd):
    #     print(f'Sending {cmd}')
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         s.connect((self.IP_ADDRESS, int(self.PORT)))
    #         s.sendall(cmd)
    #         self.message_queue.append(s.recv(1024).strip())
    #         print(f"Received:{self.message_queue[-1]}")

    def write(self, cmd):
        print(f'Sending {cmd}')
        self.conn.sendall(cmd)
        self.message_queue.append(self.conn.recv(1024).strip())
        print(f"Received:{self.message_queue[-1]}")

    def read(self):
        if self.message_queue:
            return self.message_queue.pop()
        else:
            return ''


if __name__ == '__main__':
    tel = Telnet()
    tel.write('1TS\r')
    print(tel.read())
