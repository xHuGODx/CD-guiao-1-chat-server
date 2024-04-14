"""CD Chat client program"""
import logging
import sys
import socket
import selectors
import os
import fcntl

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)

IP = "localhost"
PORT = 5000
ADDR = (IP, PORT)

class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.channel = "#General"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()

        original_flags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, original_flags | os.O_NONBLOCK)
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.send)

        print("Client initialized: " + self.name)

    def read(self, socket, mask):
        data = CDProto.recv_msg(self.sock)
        logging.debug("Message received from" + repr(self.sock))
        print(data.message)

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sock.connect(ADDR)
        self.sel.register(self.sock, selectors.EVENT_READ, self.read)
        CDProto.send_msg(self.sock, CDProto.register(self.name))

        logging.debug(self.name + " connected to " + repr(ADDR))
        print("Connected to " + repr(ADDR))
        self.join("#General")


    def send(self, stdin, mask):
        message = stdin.read()
        if message.startswith("/unjoin"):
            #implementacao basica, solicitada pelo professor, equivalente a /join #General
            self.join("#General")
        elif message.startswith("/join"):
            if len(message.split(" ")) < 2:
                print("Usage: /join <channel>")
                return
            if self.channel == message.split(" ")[1]:
                print("You are already in " + self.channel)
                return
            self.join(message.split(" ")[1])
        elif message == "exit\n":
            print("Client " + self.name + " exiting.")
            logging.debug("Client " + self.name + " exited.")
            self.sel.unregister(self.sock)
            self.sock.close()
            print("Closing chat.")
            self.sel.unregister(self.sock)
            self.sock.close()
            sys.exit(0)
        else:
            logging.debug("Client " + self.name + " tried to send: ----" + message + "----")
            CDProto.send_msg(self.sock, CDProto.message(message, self.channel))
            logging.debug("Client " + self.name + " sent: ----" + message + "----")
    
    def join(self, channel):
        if self.channel != "#General":
            self.channel = self.channel[:-1]
        print("Leaving " + self.channel + " and joining " + channel)
        logging.debug("Client " + self.name + " left " + self.channel + " and joined " + channel)
        self.channel = channel
        CDProto.send_msg(self.sock, CDProto.join(channel))
        
    def loop(self):
        """Loop indefinetely."""
        while True:
            try:
                sys.stdout.write(">")
                sys.stdout.flush()
                for key, mask in self.sel.select():
                    callback = key.data
                    callback(key.fileobj, mask)
            except KeyboardInterrupt:
                print("Client " + self.name + " exiting.")
                logging.debug("Client " + self.name + " exited.")
                self.sel.unregister(self.sock)
                self.sock.close()
                print("Closing chat.")
                sys.exit(0)