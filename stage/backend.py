import telnetlib3
import asyncio
import time
import os
from subprocess import Popen, PIPE

# @asyncio.coroutine
# def shell(reader, writer, cmd):
#     while True:
#         writer.write(cmd)
#         outp = yield from reader.read(1024)
#         if not outp:
#             break

class Telnet:

    IP_ADDRESS = '192.168.254.254'
    PORT = '5001'
    cmd_queue = []
    message_queue = []

    def __init__(self):
        nc_bin = ''
        p = Popen(["which", "nc"], stdout=PIPE)
        nc_bin = p.communicate()[0][:-1]  # Strip trailing \n
        if not os.path.exists(nc_bin):
            raise OSError("Did not find nc binary")
        self.__startnc(nc_bin)

    def __startnc(self, nc_bin):
        self.nc = Popen([nc_bin, '-t', self.IP_ADDRESS, self.PORT], stdin=PIPE, stdout=PIPE)

    def write(self, cmd):
        self.nc.communicate(cmd)

    def read(self):
        return self.nc.communicate()[0]


class OldTelnet:

    IP_ADDRESS = '192.168.254.254'
    PORT = 5001
    cmd_queue = []
    message_queue = []

    async def shell(self, reader, writer):
        _cmd = self.cmd_queue.pop()
        print(f'Sending command {_cmd}')
        writer.write(_cmd)
        print('Sent.')
        outp = await reader.readline()
        print('Read raw data.')
        if len(outp) > 1:
            await self.message_queue.append(outp[:2])
            print(f'Received: {self.message_queue[-1]}')
        else:
            print('Did not receive reply.')
        await writer.protocol.waiter_closed

    def __runloop(self):
        coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        asyncio.run(coro)
        # loop = asyncio.get_event_loop()
        # coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        # reader, writer = loop.run_until_complete(coro)
        # loop.run_until_complete(writer.protocol.waiter_closed)

    def read(self):
        i = 0
        while not len(self.message_queue):
            time.sleep(0.1)
            i++1
            if i > 10:
                return ' '
        return self.message_queue.pop()

    def write(self, cmd):
        self.cmd_queue.append(cmd)
        self.__runloop()


if __name__ == '__main__':
    tel = Telnet()
    tel.write('1TS\r')
    print(tel.read())
