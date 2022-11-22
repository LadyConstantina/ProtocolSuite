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
    def __init__(self, host, port, SECRET_KEY="PRLAB3") -> None:
        super(Leader_Server, self).__init__()
        self.Table = {}
        self.Followers = []
        self.host = host
        self.port = port
        self.SECRET_KEY = SECRET_KEY
        self.HRemail = "constantinagilca@gmail.com"
        self.operation2method = {
            "add": requests.post,
            "update": requests.put,
            "delete": requests.delete
        }

    def update_followers(self, dic, operation, index=None):
        for follower in self.Followers:
            follower_location = follower["host"] + ":" + follower["port"]
            while True:
                if index:
                    res = self.operation2method[operation](f"http://{follower_location}/application/{index}", json=dic,
                                                           headers={"Token": self.SECRET_KEY, "Leader": "True"})
                else:
                    res = self.operation2method[operation](f"http://{follower_location}/application", json=dic,
                                                           headers={"Token": self.SECRET_KEY, "Leader": "True"})
                if res.status_code == 200:
                    break

    def add_element(self, dic):
        index = str(uuid.uuid1())
        dic["index"] = index
        self.Table[index] = dic
        self.update_followers(dic, "add")
        self.send_email("New Application",dic)
        return {
                   "Index": index,
                   "Status": "OK",
                   "Code": 200
               }, 200

    def update_element(self, index, dic):
        if index in self.Table:
            self.Table[index].update(dic)
            self.update_followers(dic, "update", index)
            self.send_email("Application Updated",dic)
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
            self.update_followers(copy, "delete", index)
            return copy, 200
        else:
            return {"message": "Index not found!"}, 404

    def Add_service_server(self, dic):
        self.Followers.append(dic)
        return 200
    
    def send_email(self, subject,dic):
        outlook = win32.Dispatch('outlook.application', pythoncom.CoInitialize())
        mail = outlook.CreateItem(0)
        mail.To = self.HRemail
        mail.Subject = subject
        mail.Body = f"Name: {dic['Name']} \n Surname: {dic['Surname']} \n Status: {dic['Status']} \n Position: {dic['Position']} \n Email: {dic['Email']} \n Comments: {dic['Comments']}"
        mail.Send()

    @property
    def my_address(self):
        return {
            "host": self.host,
            "port": self.port,
        }


###=========================================================================================

class Follower_Server(Base_Server):
    def __init__(self, host, port, leader_data) -> None:
        super(Follower_Server, self).__init__()
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