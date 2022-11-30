import socket
import json

class FTPClient:
    def __init__(self, cmd_port, data_port, files_root):
        self.cmd_port = cmd_port
        self.data_port = data_port
        self.files_root = files_root
        self.cmd_sock = socket.socket()
        self.data_sock = socket.socket()
        self.cmd_sock.connect(("127.0.0.1", self.cmd_port))
        self.data_sock.connect(("127.0.0.1", self.data_port))

        self.cmd_commands = ["LIST", "RETR", "STOR"]

    def listen(self):
        self.cmd_sock.listen(20)
        self.data_sock.listen(20)

        self.cmd_conn, _ = self.cmd_sock.accept()
        self.data_conn, _ = self.data_sock.accept()

    def list(self):
        self.cmd_sock.send(b"LIST")
        list_of_files = json.loads(self.data_sock.recv(2048).decode())
        print(list_of_files)
        return list_of_files

    def retr(self, filename):
        self.cmd_sock.send(b"RETR")
        self.data_sock.send(str.encode(filename))
        data = self.data_sock.recv(2048).decode()
        if data != "":
            f = open(filename, 'w')
            f.write(data)
            f.close()

    def stor(self, filename):
        self.cmd_sock.send(b"STOR")
        binary_file = open(filename, 'rb').read()
        self.data_sock.send(str.encode(filename))
        self.data_sock.send(binary_file)

    def quit(self):
        self.cmd_sock.send(b"QUIT")
        self.cmd_sock.close()
        self.data_sock.close()

