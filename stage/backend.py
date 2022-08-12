import telnetlib3
import asyncio

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
    cmd_queue = []
    message_queue = []
    lock = asyncio.Lock()

    async def shell(self, reader, writer):
        _cmd = self.cmd_queue.pop()
        print(f'Sending command {_cmd}')
        writer.write(_cmd)
        outp = await reader.read(1024)
        if len(outp) > 1:
            self.message_queue.append(outp[:2])
        else:
            print('Did not receive reply.')

    async def __client(self):
        r, w = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT)

    def __runloop(self):
        loop = asyncio.get_event_loop()
        coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        reader, writer = loop.run_until_complete(coro)
        loop.run_until_complete(writer.protocol.waiter_closed)

    def read(self):
        async with self.lock():
            if self.message_queue:
                return self.message_queue.pop()

    def write(self, cmd):
        async with self.lock:
            self.cmd_queue.append(cmd)
            self.__runloop()


if __name__ == '__main__':
    tel = Telnet()
    tel.write('1TS\r')
    print(tel.read())
