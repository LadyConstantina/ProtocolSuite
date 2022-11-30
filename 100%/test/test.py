import requests
import socket
import json

class FTPClient:
    def __init__(self, cmd_port, data_port):
        self.cmd_port = cmd_port
        self.data_port = data_port
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

print("Please introduce the details of the application:")
name = input("Input name:")
surname = input("Input surname:")
email = input("Input email:")
position = input("Position:")
comments = input("Comments:")
status = input("Status:")
resume = input("Input the name of the resume:")

port = input("Input the port of the leader service:")

data_for_service = {
    "name" : name,
    "surname" : surname,
    "email" : email,
    "position" : position,
    "comments" : comments,
    "status" : status
}

res = requests.post(f"http://127.0.0.1:{port}/application", json=data_for_service, headers={"Token" : "PRLAB3"})

for ftp in res.json()["ftp_ports"]:
    ftp_client = FTPClient(ftp["ftp_cmd_port"], ftp["ftp_data_port"])
    ftp_client.stor(resume)
    ftp_client.quit()
print("Done!")
