import telnetlib3
import asyncio
import time

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
    tasks = set()
    cmd_queue = []
    message_queue = []

    def __init__(self):
        coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        asyncio.run(coro)

    # async def __mainloop(self):

    async def shell(self, reader, writer):
        while True:
            if not self.cmd_queue:
                await asyncio.sleep(0.1)
                continue
            _cmd = self.cmd_queue.pop()
            print(f'Sending command {_cmd}')
            writer.write(_cmd)
            outp = await reader.read(1024)
            if len(outp) > 1:
                await self.message_queue.append(outp[:2])
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

    async def __read(self):
        msg = await self.message_queue.get()
        self.message_queue.task_done()
        return msg

    async def __write(self, cmd):
        await self.cmd_queue.put(cmd)

    def read(self):
        if self.message_queue:
            return self.message_queue.pop()

    def write(self, cmd):
        self.cmd_queue.append(cmd)


if __name__ == '__main__':
    tel = Telnet()
    tel.write('1TS\r')
    print(tel.read())
