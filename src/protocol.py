"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    def __init__(self,command) -> None: #constructor base
        self.command = command
    """Message Type."""

    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self,channel) -> None: #constructor base que herda o message
        super().__init__("join")
        self.channel = channel
    
    def __repr__(self) -> str:
        data = {"command": "join", "channel": self.channel}
        return json.dumps(data)


class RegisterMessage(Message):
    def __init__(self,user) -> None:
        super().__init__("register")
        self.user = user

    def __repr__(self) -> str:
        data = {"command": "register", "user": self.user}
        return json.dumps(data)
    """Message to register username in the server."""


    
class TextMessage(Message):
    def __init__(self,message,channel, ts) -> None:
        super().__init__("message")
        self.message = message
        self.channel = channel
        self.ts = ts

    def __repr__(self) -> str:
        if self.channel == None :
            data = {"command": "message", "message": self.message,"ts":self.ts}
            return json.dumps(data)
        else:
            data = {"command": "message", "message": self.message, "channel":self.channel,"ts":self.ts}
            return json.dumps(data)

    """Message to chat with other clients."""


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        ts = int(datetime.now().timestamp())
        return TextMessage(message,channel,ts)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):      
        data = json.dumps(msg.__dict__)
        size = len(data)
        header = size.to_bytes(2, "big")
        message = header + data.encode("utf-8")
        socket.sendall(connection, message)
        """Sends through a connection a Message object."""

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        try:
            header = connection.recv(2)
            n = int.from_bytes(header, "big")
            data = connection.recv(n)
            dict = json.loads(data)
            if dict["command"] == "register":
                return cls.register(dict["user"])
            if dict["command"] == "join":
                return cls.join(dict["channel"])
            if dict["command"] == "message":
                return cls.message(dict["message"], dict.get("channel", None))
        except json.JSONDecodeError:
            raise CDProtoBadFormat(data)
        """Receives through a connection a Message object."""


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")