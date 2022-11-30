import socket
import os
import json

class FTPServer:
    def __init__(self, cmd_port, data_port, files_root):
        self.cmd_port = cmd_port
        self.data_port = data_port
        self.files_root = files_root
        self.cmd_sock = socket.socket()
        self.data_sock = socket.socket()
        self.cmd_sock.bind(("127.0.0.1", self.cmd_port))
        self.data_sock.bind(("127.0.0.1", self.data_port))

        self.cmd_commands = ["LIST", "RETR", "STOR"]

    def listen(self):
        self.cmd_sock.listen(20)
        self.data_sock.listen(20)

        self.cmd_conn, _ = self.cmd_sock.accept()
        self.data_conn, _ = self.data_sock.accept()

    def run(self):
        self.listen()
        while True:
            cmd = self.cmd_conn.recv(2048)
            if cmd.decode() == "LIST":
                list_of_files = os.listdir(self.files_root)
                to_send = json.dumps(list_of_files).encode()
                self.data_conn.send(to_send)
            elif cmd.decode() == "RETR":
                file_name = self.data_conn.recv(2048)
                if file_name.decode() in os.listdir(self.files_root):
                    binary_file = open(
                        os.path.join(self.files_root, file_name.decode()), 'rb'
                    ).read()
                    self.data_conn.send(binary_file)
            elif cmd.decode() == "STOR":
                file_name = self.data_conn.recv(2048).decode()
                file_data = self.data_conn.recv(2048).decode()
                f = open(
                    os.path.join(self.files_root, file_name), 'w'
                )
                f.write(file_data)
            elif cmd.decode() == "QUIT":
                self.cmd_conn.close()
                self.data_conn.close()
                break
