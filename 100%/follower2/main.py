from urllib3.exceptions import NewConnectionError, MaxRetryError
from config import get_configurations
from flask import Flask, request, jsonify
import requests
import uuid  # nonincremental id
from services.Factory import RAFTFactory
import threading
import logging
import json
import sys
import time
import random
from requests.adapters import HTTPAdapter
import socket
from _thread import *

requests.adapters.DEFAULT_RETRIES = 3

app = Flask(__name__)

FOLLOWERS = []

ClientSocket = None

SECRET_KEY = "PRLAB3"
configurations = get_configurations()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
root_logger.addHandler(handler)
handler = logging.FileHandler(configurations['General']["logfile"], 'a', 'utf-8')
root_logger.addHandler(handler)

factory = RAFTFactory({
    "host": configurations['General']["host"],
    "port": configurations['General']["port"],
    "angle": [int(ang) for ang in configurations["General"]["angle"].split(",")],
    "ftp_cmd_port" : int(configurations["General"]["ftp_cmd_port"]),
    "ftp_data_port" : int(configurations["General"]["ftp_data_port"])
})
Manager = factory.create_server(logger=root_logger)

def check_access_tocken(header_dict):
    if "Token" not in header_dict:
        # root_logger.error("Missing Authorization Token!")
        return {
            "Message": "Missing Authorization Token!",
            "Code": 401
        }
    elif header_dict["Token"] != SECRET_KEY:
        # root_logger.error("Unauthorised access!")
        return {
            "Message": "Unauthorised access!",
            "Code": 401
        }
    else:
        return "OK"


# Endpoint for POST requests
@app.route("/application", methods=["POST"])
def POST_Application():
    # Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    elif hasattr(Manager, "SECRET_KEY") or "Leader" in dict(request.headers):
        resp, status_code = Manager.add_element(request.json)
        for_log = request.json
        for_log["index"] = resp["Index"]
        root_logger.critical(f"POST|{time.time()}|{json.dumps(for_log)}")
        return resp, status_code
    else:
        return {
                   "Message": "Can't write to the follower!"
               }, 500


# Endpoint for GET requests -> returns all rows from applications
@app.route("/application", methods=["GET"])
def GET_Application():
    # Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        records_list = []
        records, status_code = Manager.get_all()
        for record in records:
            records_list.append(
                records[record]
            )
        return jsonify(records_list), status_code


@app.route("/application/<index>", methods=["GET"])
def GET_Application_byID(index):
    # Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        application, status_code = Manager.get_element(index)
        return application, status_code


@app.route("/application/<index>", methods=["PUT"])
def PUT_Application_byID(index):
    # Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    elif hasattr(Manager, "SECRET_KEY") or "Leader" in dict(request.headers):
        change_fields = request.json
        response, status_code = Manager.update_element(index, change_fields)
        change_fields["index"] = index
        root_logger.critical(f"PUT|{time.time()}|{json.dumps(change_fields)}")
        return response, status_code
    else:
        return {
                   "Message": "Can't write to the follower!"
               }, 500


@app.route("/application/<index>", methods=["DELETE"])
def DELETE_Application_byID(index):
    # Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    elif hasattr(Manager, "SECRET_KEY") or "Leader" in dict(request.headers):
        application, status_code = Manager.delete_element(index)
        root_logger.critical(f"DELETE|{time.time()}|{index}")
        return application, status_code
    else:
        return {
                   "Message": "Can't write to the follower!"
               }, 500


@app.route("/re-election", methods=["GET"])
def re_election():
    global ClientSocket
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        ClientSocket.close()
        return {"accept": "True"}

@app.errorhandler(500)
def exception_handler(error):
    return jsonify(error=str(error))

app.register_error_handler(500, exception_handler)

# Leader
def client_handler(connection):
    #connection.send(str.encode('You are now connected to the replay server... Type BYE to stop'))
    while True:
        data = connection.recv(2048)
        message = data.decode('utf-8')
        if message == 'BYE':
            break

        reply = json.dumps(Manager.Followers)
        connection.sendall(str.encode(reply))
    connection.close()

# Leader
def accept_connections(ServerSocket):
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(client_handler, (Client, ))

# Leader
def start_server(host, port):
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        print(str(e))
    ServerSocket.listen()

    while True:
        accept_connections(ServerSocket)

def check_heartbeat2():
    global Manager, FOLLOWERS, ClientSocket, factory

    if not hasattr(Manager, "SECRET_KEY"):
        # Follower
        host = '127.0.0.1'
        port = 7000
        ClientSocket = socket.socket()
        time.sleep(3)
        try:
            ClientSocket.connect((host, port))
        except socket.error as e:
            print(str(e))
        while True:
            try:
                ClientSocket.send(str.encode("heartbeat"))
                Response = ClientSocket.recv(2048)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                print("Closed connection")
                ClientSocket.close()
                time.sleep(random.randint(5, 10))
                for follower in FOLLOWERS:
                    if follower != Manager.my_address:
                        follower_endpoint = f"http://{follower['host']}:{follower['port']}/re-election"
                        follower_response = requests.get(follower_endpoint, headers={"Token": SECRET_KEY})

                        if follower_response.json()["accept"] == "True":
                            factory = RAFTFactory({
                                "host": configurations['General']["host"],
                                "port": configurations['General']["port"],
                                "angle": [int(ang) for ang in configurations["General"]["angle"].split(",")],
                                "ftp_cmd_port" : configurations["General"]["ftp_cmd_port"],
                                "ftp_data_port" : configurations["General"]["ftp_data_port"]
                            }, 2)

                            Manager = factory.create_server(logger=root_logger)
                            break
                break
            else:
                try:
                    FOLLOWERS = json.loads(Response.decode('utf-8'))
                except:
                    continue
                finally:
                    time.sleep(10 + random.randint(3, 4))
        check_heartbeat2()

    else:
        # Leader
        host = '127.0.0.1'
        port = 7000

        start_server(host, port)


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(
        host=configurations["General"]["host"],
        port=configurations["General"]["port"])).start()
    #threading.Thread(target=check_heartbeat).start()
    #check_heartbeat2()
    threading.Thread(target=check_heartbeat2).start()
