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
    cmd_queue = asyncio.Queue()
    message_queue = asyncio.Queue()

    async def shell(self, reader, writer):
        _cmd = await self.cmd_queue.get()
        self.cmd_queue.task_done()
        print(f'Sending command {_cmd}')
        writer.write(_cmd)
        outp = await reader.read(1024)
        if len(outp) > 1:
            await self.message_queue.put(outp[:2])
        else:
            print('Did not receive reply.')

    def __runloop(self):
        coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        asyncio.run(coro)
        #loop = asyncio.get_event_loop()
        #coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        #reader, writer = loop.run_until_complete(coro)
        #loop.run_until_complete(writer.protocol.waiter_closed)
        

    async def read(self):
        msg = await self.message_queue.get()
        self.message_queue.task_done()
        print(msg)
        return msg

    async def write(self, cmd):
        await self.cmd_queue.put(cmd)
        self.__runloop()


if __name__ == '__main__':
    tel = Telnet()
    tel.write('1TS\r')
    print(tel.read())
