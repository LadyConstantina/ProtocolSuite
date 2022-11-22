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
from requests.adapters import HTTPAdapter, Retry

requests.adapters.DEFAULT_RETRIES = 3

app = Flask(__name__)

FOLLOWERS = []

SECRET_KEY = "PRLAB3"
configurations = get_configurations()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
root_logger.addHandler(handler)
handler = logging.FileHandler(configurations['General']["logfile"], 'a', 'utf-8')
root_logger.addHandler(handler)

time.sleep(random.randint(2, 5))
factory = RAFTFactory({
    "host": configurations['General']["host"],
    "port": configurations['General']["port"]
})

Manager = factory.create_server()
print(Manager.Followers)


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
    else:
        resp, status_code = Manager.add_element(request.json)
        for_log = request.json
        for_log["index"] = resp["Index"]
        root_logger.debug(f"POST|{json.dumps(for_log)}")
        return resp, status_code


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
    elif configurations["General"]["leader"] or "Leader" in dict(request.headers):
        change_fields = request.json
        response, status_code = Manager.update_element(index, change_fields)
        change_fields["index"] = index
        root_logger.debug(f"PUT|{json.dumps(change_fields)}")
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
    elif configurations["General"]["leader"] or "Leader" in dict(request.headers):
        application, status_code = Manager.delete_element(index)
        root_logger.debug(f"DELETE|{index}")
        return application, status_code
    else:
        return {
                   "Message": "Can't write to the follower!"
               }, 500


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        return jsonify(Manager.Followers)


@app.route("/re-election", methods=["GET"])
def re_election():
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        return {"accept": "True"}


def check_heartbeat():
    global Manager, FOLLOWERS

    while True:
        if not hasattr(Manager, "SECRET_KEY"):
            leader_endpoint = f"http://{Manager.leader_data['host']}:{Manager.leader_data['port']}/heartbeat"

        if not hasattr(Manager, "SECRET_KEY"):
            try:
                '''''
                s = requests.Session()
                retries = Retry(total=1, backoff_factor=1, status_forcelist=[502, 503, 504])
                s.mount('http://', HTTPAdapter(max_retries=retries))

                s.get(leader_endpoint, headers={"Token": SECRET_KEY})
                '''
                response = requests.get(leader_endpoint, headers={"Token": SECRET_KEY})
            except Exception as nce:
                print("Exception")
                for follower in FOLLOWERS:
                    print("Follower")
                    print(follower)
                    if follower != Manager.my_address:
                        print(follower)
                        follower_endpoint = f"http://{follower['host']}:{follower['port']}/re-election"
                        follower_response = requests.get(follower_endpoint, headers={"Token": SECRET_KEY})

                        if follower_response.json()["accept"] == "True":
                            factory = RAFTFactory({
                                "host": configurations['General']["host"],
                                "port": configurations['General']["port"]
                            })

                            Manager = factory.create_server()
                            print(Manager.Followers)
            else:
                FOLLOWERS = response.json()
                print("FOLOWERS")
                print(FOLLOWERS)
                time.sleep(15 + random.randint(1, 3))


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(
        host=configurations["General"]["host"],
        port=configurations["General"]["port"])).start()
    threading.Thread(target=check_heartbeat).start()

