import telnetlib3
import asyncio

# @asyncio.coroutine
# def shell(reader, writer, cmd):
#     while True:
#         writer.write(cmd)
#         outp = yield from reader.read(1024)
#         if not outp:
#             break

r_closed
    return protocol.stream.read()

class Telnet:

    IP_ADDRESS = '192.168.254.254'
    PORT = 5001
    message_queue = []

    # def __init__(self):
        # self.reader, self.writer = telnetlib3.open_connection(host=self.IP_ADDRESS, port=self.PORT)

    def __getclient(self):
        return telnetlib3.TelnetClient(encoding='utf-8', shell=telnetlib3.TerminalShell)

    @asyncio.coroutine
    def __register_telnet_client(self, loop, Client, host, port, command):
        transport, protocol = yield from loop.create_connection(Client, host, port)
        print("{} async connection OK for command {}".format(host, command))

        def send_command():
            EOF = chr(4)
            EOL = '\n'
            # adding newline and end-of-file for this simple example
            command_line = command + EOL + EOF
            protocol.stream.write(protocol.shell.encode(command_line))

        # one shot invocation of the command
        loop.call_soon(send_command)
        self.message_queue.append(rotocol.stream.read())
        # what does this do exactly ?
        yield from protocol.waiter_closed

    def __runloop(self, cmd):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.__register_telnet_client(loop, self.__getclient,
                                          host=self.IP_ADDRESS,
                                          port=self.PORT,
                                          command=cmd
                                          )
        )

    def read(self):
        return self.message_queue.pop()

    def write(self, cmd):
        self.__runloop(cmd)


if __name__ == '__main__':
    tel = Telnet()
    tel.write(b'TS\r')
    print(tel.read())