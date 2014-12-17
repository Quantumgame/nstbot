import socket
import re
import inspect

class Command(object):
    def __init__(self, regex, function, code, desc):
        self.matcher = re.compile(regex)
        self.function = function
        self.code = code
        self.desc = desc
    def __call__(self, server, msg):
        m = self.matcher.match(msg)
        if m is None:
            return False
        else:
            self.function(server, *m.groups())

def command(pattern, code, desc):
    def command_decorator(func):
        return Command(pattern, func, code, desc)
    return command_decorator


class NSTServer(object):
    def __init__(self, port=56000, buffer_size=1024):
        self.port = port
        self.buffer_size = buffer_size

        self.commands = {}
        for name, func in inspect.getmembers(self):
            if isinstance(func, Command):
                self.commands[name] = func

    def send(self, msg):
        self.conn.sendall(msg + '\r\n')

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', self.port))  # allow connections from anywhere
        self.socket.listen(1)              # only allow one connection

        while True:
            try:
                self.conn, self.addr = self.socket.accept()
                self.send(self.welcome_message())
                self.conn.recv(self.buffer_size)   # try to empty the buffer
                msg = ''
                while True:
                    msg = msg + self.conn.recv(self.buffer_size)
                    if len(msg) == 0:
                        # client has disconnected
                        break
                    index = msg.find('\n')
                    while index > -1:
                        cmd = msg[:index]
                        msg = msg[index + 1:]
                        self.process_command(cmd.strip())
                        index = msg.find('\n')
            finally:
                self.conn.close()

    def welcome_message(self):
        return '''NST robot interface.  Type '??' and hit <enter> for help.'''

    def process_command(self, cmd):
        print 'processing command:', `cmd`
        for command in self.commands.values():
            success = command(self, cmd)
            if success:
                break

    @command('[?][?]', '??', 'show help')
    def help(self):
        self.send('Available commands:')
        for name, c in sorted(self.commands.items()):
            line = ' %-12s %s' % (c.code, c.desc)
            self.send(line)

    @command('quit', 'quit', 'stop the server')
    def quit(self):
        self.send("exiting...")
        import sys
        sys.exit()

    @command(r'echo(\d+)', 'echo###', 'print the given number')
    def echo(self, value):
        self.send('value: "%s"' % value)




if __name__ == '__main__':
    NSTServer().run()



