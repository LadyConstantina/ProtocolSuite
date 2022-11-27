import requests
import uuid
import win32com.client as win32
import pythoncom


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


class Leader_Server(Base_Server):
    def __init__(self, host, port, angle, SECRET_KEY="PRLAB3") -> None:
        super(Leader_Server, self).__init__()
        self.angle = angle
        self.Table = {}
        self.Followers = []
        self.host = host
        self.port = port
        self.SECRET_KEY = SECRET_KEY
        self.HRemail = "constantinagilca@gmail.com"
        self.operation2method = {
            "add": requests.post,
            "update": requests.put,
            "delete": requests.delete,
            "get" : requests.get
        }
    
    def redirect(self, index):
        data_hash = hash(index)
        hash_mod_360 = data_hash % 360
        print(hash_mod_360)
        choosed_grade = 0
        min_dist = 360
        for grades in [0, 120, 240]:
            diff = abs(grades - hash_mod_360)
            if diff < min_dist:
                choosed_grade = grades
        responsible_services = []
        if choosed_grade == int(self.angle):
            responsible_services.append("me")
        for i in range(len(self.Followers)):
            if choosed_grade == int(self.Followers[i]["angle"]):
                responsible_services.append(i)
        print(responsible_services)
        return responsible_services

    def update_followers(self, dic, operation, i, index=None):
        follower_location = self.Followers[i]["host"] + ":" + self.Followers[i]["port"]
        while True:
            if index:
                res = self.operation2method[operation](f"http://{follower_location}/application/{index}", json=dic,
                                                        headers={"Token": self.SECRET_KEY, "Leader": "True"})
            else:
                res = self.operation2method[operation](f"http://{follower_location}/application", json=dic,
                                                           headers={"Token": self.SECRET_KEY, "Leader": "True"})
            if res.status_code == 200:
                break
        if operation == "get":
            return res

    def add_element(self, dic):
        index = str(uuid.uuid1())
        dic["index"] = index
        resp_services = self.redirect(index)

        for resp in resp_services:
            if resp == 'me':        
                self.Table[index] = dic
            else:
                self.update_followers(dic, "add", resp)
        return {
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
            else:
                self.update_followers(dic, "update", resp, index)
            return self.Table[index], 200
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
            res = self.update_followers({}, "get", resp_services[0], index)
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
            else:
                self.update_followers(copy, "delete", resp, index)
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
        }


###=========================================================================================

class Follower_Server(Base_Server):
    def __init__(self, host, port, angle, leader_data) -> None:
        super(Follower_Server, self).__init__()
        self.angle=angle
        self.Table = {}
        self.host = host
        self.port = port
        self.Followers = []
        self.leader_data = leader_data

    def add_element(self, dic):
        index = dic["index"]
        self.Table[index] = dic
        return {
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
            "port": self.port
        }