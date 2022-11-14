from config import get_configurations
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate
import requests
import uuid #nonincremental id

app = Flask(__name__)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)
migrate = Migrate(app,db)
manager = Manager(app)

SECRET_KEY = "PRLAB3"
configurations = get_configurations()
if configurations["General"]["leader"] == "true" :
    configurations["General"]["leader"] = True
else :
    configurations["General"]["leader"] = False

Followers = {
    "Me" : configurations["General"]["leader"],
    "leader:3000" : True,
    "follower2:5000" : False
}

def check_access_tocken(header_dict):
    if "Token" not in header_dict:
        return {
            "Message": "Missing Authorization Token!",
            "Code": 401
        }
    elif header_dict["Token"] != SECRET_KEY:
        return{
            "Message": "Unauthorised access!",
            "Code": 401
        }
    else:
        return "OK"
    
class Application(db.Model):

    #Table creation
    ID = db.Column(db.String(64), primary_key = True)
    Name = db.Column(db.String(32), unique = False)
    Surname = db.Column(db.String(32), unique = False)
    Email = db.Column(db.String(32), unique = False)
    Comments = db.Column(db.String(1024), unique = False)
    Position = db.Column(db.String(32), unique = False)
    Status = db.Column(db.String(32), unique = False)

@app.before_first_request
def create_tables():
    db.create_all()

#Endpoint for POST requests
@app.route("/application",methods = ["POST"])
def POST_Application():
    #Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        if configurations["General"]["leader"] :
            index = str(uuid.uuid1())
        elif not configurations["General"]["leader"] and "Leader" in dict(request.headers):
            index  = request.json["ID"]
        else:
            return {
                "Message": "Can't write to the follower!"
            }, 500
        #Create the new applicant
        new_application = Application(
            ID = index, 
            Name = request.json["Name"],
            Surname = request.json["Surname"],
            Email = request.json["Email"],
            Comments = request.json["Comments"],
            Position = request.json["Position"],
            Status = request.json["Status"]
            )
        db.session.add(new_application)
        db.session.commit()
        if configurations["General"]["leader"]:
            json_data = request.json
            json_data["ID"] = index
            for service in Followers:
                if service != "Me":
                    while True:
                        res = requests.post(f"http://{service}/application",json = json_data, headers = {"Token":SECRET_KEY, "Leader": "True"})
                        if res.status_code == 200:
                            break
    return {
        "Index":index,
        "Status":"OK",
        "Code": 200
    },200
    
#Endpoint for GET requests -> returns all rows from applications
@app.route("/application",methods = ["GET"])
def GET_Application():
    #Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        records_list = []
        records = Application.query.all()
        for record in records:
            record_dict = record.__dict__
            del record_dict["_sa_instance_state"]
            records_list.append(
                record.__dict__
            )
        return jsonify(records_list), 200

@app.route("/application/<index>",methods = ["GET"])
def GET_Application_byID(index):
    #Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    else:
        application = Application.query.filter_by(ID = index).first()
        if application :
            application_dict = application.__dict__
            del application_dict["_sa_instance_state"]
            return application_dict,200
        else:
            return {}, 200

@app.route("/application/<index>",methods = ["PUT"])
def PUT_Application_byID(index):
    #Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    elif configurations["General"]["leader"] or "Leader" in dict(request.headers):
        application = Application.query.filter_by(ID = index).first()
        if application:
            change_fields = request.json
            for key,value in change_fields.items():
                setattr (application, key, value) #setting the attribution key of application to value
            db.session.commit()
            if configurations["General"]["leader"]:
                json_data = request.json
                for service in Followers:
                    if service != "Me":
                        while True:
                            res = requests.put(f"http://{service}/application/{index}",json = json_data, headers = {"Token":SECRET_KEY, "Leader": "True"})
                            if res.status_code == 200:
                                break
            return {
                "ID": application.ID,
                "Name": application.Name,
                "Surname": application.Surname,
                "Email": application.Email,
                "Comments": application.Comments,
                "Position": application.Position,
                "Status": application.Status
            },200
        else:
            return {
                "Message": "Index not found!",
                "Code": 404
            }, 404
    else:
        return {
                "Message": "Can't write to the follower!"
            }, 500

@app.route("/application/<index>",methods = ["DELETE"])
def DELETE_Application_byID(index):
    #Check the access authorisation
    check_response = check_access_tocken(dict(request.headers))
    if check_response != "OK":
        return check_response
    elif configurations["General"]["leader"] or "Leader" in dict(request.headers):
        application = Application.query.filter_by(ID = index).first()
        if application:
            db.session.delete(application)
            db.session.commit()
            if configurations["General"]["leader"]:
                for service in Followers:
                    if service != "Me":
                        while True:
                            res = requests.delete(f"http://{service}/application/{index}", headers = {"Token":SECRET_KEY, "Leader": "True"})
                            if res.status_code == 200:
                                break
            return {
                "ID": application.ID,
                "Name": application.Name,
                "Surname": application.Surname,
                "Email": application.Email,
                "Comments": application.Comments,
                "Position": application.Position,
                "Status": "Deleted"
            },200
        else:
            return {
                "Message": "Index not found!",
                "Code": 404
            }, 404
    else:
        return {
                "Message": "Can't write to the follower!"
            }, 500

app.run(host = "0.0.0.0",port = configurations["General"]["port"])

    

