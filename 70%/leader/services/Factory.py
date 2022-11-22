from .ServiceManager import Follower_Server, Leader_Server
import socket
import json

class AbstractFactory:
    def create_server(self,service_type, **kwargs):
        pass

class Factory(AbstractFactory):
    def create_server(self, service_type, **kwargs):
        if service_type == "leader":
            return Leader_Server(kwargs["host"], kwargs["port"], kwargs["leader"])
        else:
            return Follower_Server(kwargs["host"], kwargs["port"], kwargs["leader"])

class RAFTFactory:
    def __init__(self, data, host="127.0.0.1", port=4444, buffer_size=1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.data = data
        try:
            self.udp_socket.bind((self.host, self.port))
            self.state = "leader"
            self.followers = []
            count_of_msgs = 0
            while True:
                bytes_adress_pair = self.udp_socket.recvfrom(buffer_size)
                message = bytes_adress_pair[0]
                address = bytes_adress_pair[1]
                print(message)
                if message.decode() == "Accept":
                    data = json.dumps(self.data)
                    count_of_msgs += 1
                    self.udp_socket.sendto(str.encode(data), address)
                else:
                    message = message.decode()
                    count_of_msgs += 1
                    print(count_of_msgs)
                    follower_data = json.loads(message)
                    self.followers.append(follower_data)
                if count_of_msgs >= 4:
                    break
        except:
            self.state = "follower"

            self.leader_data = self.send_accept("Accept")
            self.send_accept(self.data)
        self.udp_socket.close()

    def create_server(self):
        if self.state == "leader":
            server = Leader_Server(self.data["host"], self.data["port"])

            for follower in self.followers:
                if follower != "Accept":
                    server.Add_service_server(follower)
        else:
            print("Leader data")
            print(self.leader_data)
            server = Follower_Server(self.data["host"], self.data["port"], self.leader_data)
        return server

    def send_accept(self, msg):
        if type(msg) is str:
            print("str")
            bytes_to_send = str.encode(msg)
            self.udp_socket.sendto(bytes_to_send, (self.host, self.port))
            msg_from_server = self.udp_socket.recvfrom(self.buffer_size)[0]
            return json.loads(msg_from_server.decode())
        else:
            print("dict")
            str_dict = json.dumps(msg)
            bytes_to_send = str.encode(str_dict)
            self.udp_socket.sendto(bytes_to_send, (self.host, self.port))