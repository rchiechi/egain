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

    def __getclient(self):
        return telnetlib3.TelnetClient(encoding='utf-8', shell=telnetlib3.telnet_client_shell)

#     async def __register_telnet_client(self, loop, Client, host, port, command):
#         transport, protocol = yield from loop.create_connection(Client, host, port)
#         print("{} async connection OK for command {}".format(host, command))
# 
#         def send_command():
#             EOF = chr(4)
#             EOL = '\n'
#             # adding newline and end-of-file for this simple example
#             command_line = command + EOL + EOF
#             protocol.stream.write(protocol.shell.encode(command_line))
# 
#         # one shot invocation of the command
#         loop.call_soon(send_command)
#         self.message_queue.append(protocol.stream.read())
#         # what does this do exactly ?
#         # yield from protocol.waiter_closed
# 
    async def shell(self, reader, writer):
        writer.write(self.cmd_queue.pop())
        outp = await reader.read(1024)
        if outp:
            self.message_queue.append(outp)

    async def __client(self):
        r, w = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT)

    def __runloop(self):
        loop = asyncio.get_event_loop()
        # r, w = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT)
        coro = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT, shell=self.shell)
        reader, writer = loop.run_until_complete(coro)
        loop.run_until_complete(writer.protocol.waiter_closed)
        # reader, writer = asyncio.run(self.__client())
        # writer.write(cmd)
        # self.message_queue.append(reader.read(1024))
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(
        #     self.__register_telnet_client(loop, self.__getclient,
        #                                   host=self.IP_ADDRESS,
        #                                   port=self.PORT,
        #                                   command=cmd
        #                                   )
        # )

    def read(self):
        return self.message_queue.pop()

    def write(self, cmd):
        self.cmd_queue.put(cmd)
        self.__runloop()


if __name__ == '__main__':
    tel = Telnet()
    tel.write(b'TS\r')
    print(tel.read())