import threading
import requests
import uuid
import json
from .ftp_server import FTPServer


class Base_Server:
    def add_element(self, dic):
        pass

    def update_element(self, index, dic):
        pass

    def get_all(self):
        pass

    def get_element(self, index):
        pass

    def delete_element(self, index):
        pass

    def get_logs(self):
        lines = open("logs.log", 'r').readlines()
        usefull_logs = []
        for line in lines:
            if line.split("|")[0] in ["UPDATE", "POST", "PUT"]:
                usefull_logs.append(line[:-1])
        return usefull_logs

    def get_last_log_id(self, logs):
        max_log = 0
        for log in logs:
            log_id = int(log.split("|")[1])
            max_log = max(max_log, log_id)
        return max_log


class Leader_Server(Base_Server):
    def __init__(self, host, port, angle, ftp_cmd_port, ftp_data_port, logger, SECRET_KEY="PRLAB3") -> None:
        super(Leader_Server, self).__init__()
        self.angle = angle
        self.Table = {}
        self.Followers = []
        self.host = host
        self.port = port
        self.ftp_cmd_port = int(ftp_cmd_port)
        self.ftp_data_port = int(ftp_data_port)
        self.SECRET_KEY = SECRET_KEY
        self.HRemail = "constantinagilca@gmail.com"
        self.operation2method = {
            "add": requests.post,
            "update": requests.put,
            "delete": requests.delete,
            "get" : requests.get
        }
        self.logger = logger
        self.op_id = 0

    def redirect(self, index):
        data_hash = hash(index)
        hash_mod_360 = data_hash % 360
        choosed_grade = 0
        min_dist = 360
        for grades in [0, 120, 240]:
            diff = abs(grades - hash_mod_360)
            if diff < min_dist:
                choosed_grade = grades
                min_dist = diff
        responsible_services = []
        if choosed_grade in self.angle:
            responsible_services.append("me")
        for i in range(len(self.Followers)):
            if choosed_grade in self.Followers[i]["angle"]:
                responsible_services.append(i)
        return responsible_services

    def update_followers(self, dic, operation, i, op_id, index=None):
        follower_location = self.Followers[i]["host"] + ":" + self.Followers[i]["port"]
        while True:
            if index:
                res = self.operation2method[operation](f"http://{follower_location}/application/{index}", json=dic,
                                                       headers={"Token": self.SECRET_KEY, "Leader": "True", "op_id" : str(op_id)})
            else:
                res = self.operation2method[operation](f"http://{follower_location}/application", json=dic,
                                                       headers={"Token": self.SECRET_KEY, "Leader": "True", "op_id" : str(op_id)})
            if res.status_code == 200:
                break
            break
        if operation in ["add", "get", "update", "delete"]:
            return res

    def add_element(self, dic):
        index = str(uuid.uuid1())
        dic["index"] = index
        resp_services = self.redirect(index)
        ftp_ports = []
        for resp in resp_services:
            if resp == 'me':
                self.Table[index] = dic
                self.logger.critical(f"POST|{self.op_id}|{json.dumps(self.Table[index])}")
                self.op_id +=1
                threading.Thread(target=FTPServer(
                    self.ftp_cmd_port, self.ftp_data_port, r"C:\Users\User\Desktop\PR3\PR3_LAB-main\100%\leader\media"
                ).run).start()
                ftp_ports.append({
                    "ftp_cmd_port" : self.ftp_cmd_port,
                    "ftp_data_port" : self.ftp_data_port
                })
            else:
                res = self.update_followers(dic, "add", resp, self.op_id)
                ftp_ports.append({
                    "ftp_cmd_port" : res.json()["ftp_cmd_port"],
                    "ftp_data_port" : res.json()["ftp_data_port"]
                })
            print(ftp_ports)
        return {
                   "ftp_ports" : ftp_ports,
                   "Index": index,
                   "Status": "OK",
                   "Code": 200
               }, 200

    def update_element(self, index, dic):
        resp_services = self.redirect(index)
        for resp in resp_services:
            if resp == "me":
                if index in self.Table:
                    self.Table[index].update(dic)
                    for_log = dic.copy()
                    for_log['index'] = index
                    self.logger.critical(f"PUT|{self.op_id}|{json.dumps(for_log)}")
                    self.op_id+=1
                    if len(resp_services) == 1:
                        return self.Table[index], 200
            else:
                res = self.update_followers(dic, "update", resp, self.op_id, index)
                return res.json(), res.status_code
        else:
            return {"message": "Index not found!"}, 404

    def get_all(self):
        return self.Table, 200

    def get_element(self, index):
        resp_services = self.redirect(index)
        if "me" in resp_services:
            if index in self.Table:
                return self.Table[index], 200
            else:
                return {"message": "Index not found!"}, 404
        else:
            res = self.update_followers({}, "get", resp_services[0], self.op_id, index)
            if res.status_code == 200:
                return res.json(), 200
            else:
                return {
                           "message" : "error"
                       }, res.status_code

    def delete_element(self, index):
        resp_services = self.redirect(index)
        for resp in resp_services:
            if resp == "me":
                if index in self.Table:
                    copy = self.Table[index].copy()
                    del self.Table[index]
                    self.logger.critical(f"DELETE|{self.op_id}|{index}")
                    self.op_id+=1
                    if len(resp_services) == 1:
                        return copy, 200
            else:
                res = self.update_followers({}, "delete", resp, self.op_id, index)
                return res.json(), res.status_code
        else:
            return {"message": "Index not found!"}, 404

    def Add_service_server(self, dic):
        self.Followers.append(dic)
        return 200

    @property
    def my_address(self):
        return {
            "host": self.host,
            "port": self.port,
        }


###=========================================================================================

class Follower_Server(Base_Server):
    def __init__(self, host, port, angle, leader_data, ftp_cmd_port, ftp_data_port, logger) -> None:
        super(Follower_Server, self).__init__()
        self.angle = angle
        self.Table = {}
        self.host = host
        self.port = port
        self.Followers = []
        self.leader_data = leader_data
        self.logger = logger
        self.ftp_cmd_port = int(ftp_cmd_port)
        self.ftp_data_port = int(ftp_data_port)

    def add_element(self, dic):
        index = dic["index"]
        self.Table[index] = dic
        threading.Thread(target=FTPServer(
            self.ftp_cmd_port, self.ftp_data_port, r"D:\70v2\leader\media"
        ).run).start()
        return {
                   "ftp_cmd_port" : self.ftp_cmd_port,
                   "ftp_data_port" : self.ftp_data_port,
                   "Index": index,
                   "Status": "OK",
                   "Code": 200
               }, 200

    def update_element(self, index, dic):
        if index in self.Table:
            self.Table[index].update(dic)
            return self.Table[index], 200
        else:
            return {"message": "Index not found!"}, 404


    def get_all(self):
        return self.Table, 200

    def get_element(self, index):
        if index in self.Table:
            return self.Table[index], 200
        else:
            return {"message": "Index not found!"}, 404

    def delete_element(self, index):
        if index in self.Table:
            copy = self.Table[index].copy()
            del self.Table[index]
            return copy, 200
        else:
            return {"message": "Index not found!"}, 404

    def Add_service_server(self, dic):
        self.Followers.append(dic)
        return 200

    @property
    def my_address(self):
        return {
            "host": self.host,
            "port": self.port,
            "angle" : self.angle
        }