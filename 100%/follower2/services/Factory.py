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
    def __init__(self, data, msgs=4, host="127.0.0.1", port=4444, buffer_size=1024):
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
                if count_of_msgs >= msgs:
                    break
        except:
            self.state = "follower"

            self.leader_data = self.send_accept("Accept")
            self.send_accept(self.data)
        self.udp_socket.close()

    def create_server(self, logger):
        if self.state == "leader":
            print("----------------LEADER----------------")
            server = Leader_Server(self.data["host"], self.data["port"], self.data["angle"],
                                   self.data["ftp_cmd_port"], self.data["ftp_data_port"], logger)

            for follower in self.followers:
                if follower != "Accept":
                    server.Add_service_server(follower)
        else:
            print("----------------FOLLOWER----------------")
            server = Follower_Server(self.data["host"], self.data["port"], self.data["angle"], self.leader_data,
                                     self.data["ftp_cmd_port"], self.data["ftp_data_port"], logger)
        return server

    def send_accept(self, msg):
        if type(msg) is str:
            bytes_to_send = str.encode(msg)
            self.udp_socket.sendto(bytes_to_send, (self.host, self.port))
            msg_from_server = self.udp_socket.recvfrom(self.buffer_size)[0]
            return json.loads(msg_from_server.decode())
        else:
            str_dict = json.dumps(msg)
            bytes_to_send = str.encode(str_dict)
            self.udp_socket.sendto(bytes_to_send, (self.host, self.port))