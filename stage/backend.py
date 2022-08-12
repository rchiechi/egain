import telnetlib3


# @asyncio.coroutine
# def shell(reader, writer, cmd):
#     while True:
#         writer.write(cmd)
#         outp = yield from reader.read(1024)
#         if not outp:
#             break


class Telnet:

    IP_ADDRESS = '192.168.254.254'
    PORT = 5001

    def __init__(self):
        self.reader, self.writer = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT)

    def read(self):
        return self.reader.readline()

    def write(self, cmd):
        self.writer.write(cmd)


if __name__ == '__main__':
    tel = Telnet()
    tel.write(b'TS\r')
    print(tel.read())