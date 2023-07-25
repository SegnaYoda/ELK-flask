import os

from flask import Flask, request, jsonify
from dotenv import load_dotenv

from flask.wrappers import Request
from flask_migrate import Migrate
import flask_praetorian
import flask_cors
from flask_mail import Mail

from models import User, db
from apm_middleware import app, ElasticAPMMiddleware
import json
import elasticapm
from elasticapm.contrib.flask import ElasticAPM


# Initialize flask app for the example
app = Flask(__name__)

app.config["ELASTIC_APM"] = {
    "SERVICE_NAME": "apm_system",
    "SECRET_TOKEN": "nIncXi7cSf8e43lvV4SE",
    "SERVER_URL": "http://apm-server:8200",
    "DEBUG": True,
    "CAPTURE_BODY": True,
}

apm = ElasticAPM(app)

apm_middleware = ElasticAPMMiddleware(app)


@app.before_request
def before_request():
    apm_middleware.capture_request_body()

@app.after_request
def after_request(response):
    apm_middleware.capture_response_body(response)
    return response

load_dotenv()


APP_NAME = os.getenv("APP_NAME")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT  = os.getenv("MAIL_PORT")
MAIL_USERNAME  = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD  = os.getenv("MAIL_PASSWORD")
SUBJECT = os.getenv("SUBJECT")
SUBJECT_RESET = os.getenv("SUBJECT_RESET")
CONFIRMATION_URI = os.getenv("CONFIRMATION_URI")
RESET_URI = os.getenv("RESET_URI")




app.debug = True
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_ACCESS_LIFESPAN"] = {"hours": 24}
app.config["JWT_REFRESH_LIFESPAN"] = {"days": 30}
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)





# Initializes CORS so that the api_tool can talk to the example app
cors = flask_cors.CORS()
cors.init_app(app)


# Initialize the flask-praetorian instance for the app
guard = flask_praetorian.Praetorian()
guard.init_app(app, User)

# Initialize the database
migrate = Migrate(app, db)


# configuration of mail
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = (APP_NAME, MAIL_USERNAME)
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

#Initialize Mail extension
mail = Mail()
mail.init_app(app)




if __name__ == "__main__":
    db.create_all()
    app.debug = True
    app.run(threaded=True)
