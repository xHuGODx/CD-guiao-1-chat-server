"""CD Chat server program."""
import logging
import socket
import selectors
import json
from datetime import datetime
from src.protocol import CDProto

logging.basicConfig(filename="server.log", level=logging.DEBUG)


IP = "localhost"
PORT = 5000
ADDR = (IP, PORT)

class Server:

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(ADDR)
        self.guestnumber = 1
        self.sock.listen(100)
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        self.clients = {}
        self.channels = {}

        print("Server initialized")
        logging.debug("Server initialized")



    def read(self,conn, mask):
        header = conn.recv(2)
        n = int.from_bytes(header, "big")
        data = conn.recv(n)

        if data:
            print('echoing', repr(data), 'to', conn)
            try:
                dict = json.loads(data)
            except json.JSONDecodeError:
                print("CDProtobadformat")
                return
            
            command = dict["command"]

            if command == "register":
                user = dict["user"]

                if user == None:
                    user = "Guest" + str(self.guestnumber)
                    self.guestnumber += 1
                
                self.clients[conn] = user
                self.channels[conn] = "#General"
                print('User: ' + user + ' register with success')
                logging.debug(user + " has joined the chat")

            elif command == "join":
                channel = dict["channel"]
                if channel == None:
                    channel = "#General"
                self.channels[conn] = channel
                print(self.clients[conn] + " joined channel " + channel)
                logging.debug(self.clients[conn] + " joined channel " + channel)

            elif command == "message":
                message = dict["message"]
                if message == None:
                    print("Cannot send message. Invalid Message")
                else:
                    channel = dict["channel"]
                    if channel == None:
                        channel = "#General"
                    for clients in self.clients:
                        if self.channels[clients] == channel and clients:
                            #remove the \n from the channel
                            if channel != "#General":
                                channel1 = channel[:-1]
                            else:
                                channel1 = "#General"
                            
                            content = str(str(self.clients[conn]) +" (" + channel1 + ")" +" @ " + str(datetime.fromtimestamp(dict["ts"])) + ": " + message)
                            
                            CDProto.send_msg(clients, CDProto.message(content))
                            
                            print(self.clients[conn] + " sent message to " + channel)
                            logging.debug(self.clients[conn] + " sent message to " + channel)
                        
            else:
                print("Invalid Command")

        else:
            print('closing', conn)
            logging.debug("Client disconnected")
            del self.clients[conn]
            del self.channels[conn]
            self.sel.unregister(conn)
            conn.close()
    """Chat Server process.el = selectors"""

    def accept(self, sock, mask):
        conn, addr = sock.accept() 
        logging.debug("Client connected")
        print('accepted', conn, 'from', addr)
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)



    def loop(self):
        """Loop indefinetely."""
        while True:
            try:
                events = self.sel.select()
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
            except KeyboardInterrupt:
                print("Server shutting down")
                logging.debug("Server shutting down")
                self.sel.close()
                self.sock.close()
                exit(0)
        
