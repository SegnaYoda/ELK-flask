import os
import logging
from logging.handlers import RotatingFileHandler
from flask import request, jsonify
from dotenv import load_dotenv

from flask.wrappers import Request
from flask_migrate import Migrate
import flask_praetorian
import flask_cors
from flask_mail import Mail

from models import User, db
from apm_middleware import app, ElasticAPMMiddleware, apm


apm_middleware = ElasticAPMMiddleware(app, apm)


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


# Set up some routes for the example
@app.get("/api")
def home():
    return jsonify({"JWT Server Application":"Running!"}), 200


@app.post("/api/login")
def login():
    """
    Logs a user in by parsing a POST request containing user credentials and
    issuing a JWT token.
    .. example::
       $ curl http://localhost:5000/api/login -X POST \
         -d "{"username":"myusername","password":"mypassword"}"
    """
    req = request.get_json(force=True)

    username = req.get("username")
    password = req.get("password")
    user = db.session.query(User).filter_by(username=username).first()

    if user:
        app.logger.info(user.username)
        if guard._verify_password(password, user.password):
            ret = {"access_token": guard.encode_jwt_token(user, bypass_user_check=True, is_registration_token=True)}
            app.logger.info(ret)
            return (jsonify(ret), 200)
        else:
            ret = {"access_token": ""}
            app.logger.info(ret)
            return (jsonify(ret), 401)
    else:
        ret = {"access_token": ""}
        return (jsonify(ret), 401)

  
@app.get("/api/refresh")
@flask_praetorian.auth_required
def refresh():
    """
    Refreshes an existing JWT by creating a new one that is a copy of the old
    except that it has a refreshed access expiration.
    .. example::
       $ curl http://localhost:5000/api/refresh -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    app.logger.warning("refresh request")
    old_token = guard.read_token_from_header()
    new_token = guard.refresh_jwt_token(old_token)
    ret = {"access_token": new_token}
    return ret, 200
  
  
@app.route("/api/protected")
@flask_praetorian.auth_required
def protected():
    """
    A protected endpoint. The auth_required decorator will require a header
    containing a valid JWT
    .. example::
       $ curl http://localhost:5000/api/protected -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    return {"message": "protected endpoint (allowed usr {})".format(flask_praetorian.current_user().username)}


@app.post("/api/registration")
def registration():
    """Register user with validation email"""
    subject = SUBJECT
    confirmation_sender=(APP_NAME, MAIL_USERNAME)
    confirmation_uri = CONFIRMATION_URI
    
    req = request.get_json(force=True)
    username = req.get("username", None)
    password = req.get("password", None)
    email = req.get("email", None)

    if db.session.query(User).filter_by(username=username).count() < 1:
        if db.session.query(User).filter_by(email=email).count() < 1:
            new_user = User(
                username=username,
                email=email,
                password=guard.hash_password(password),
                roles="user",
            )
            db.session.add(new_user)
            db.session.commit()
        
            # guard.send_registration_email(email, user=new_user, confirmation_sender=confirmation_sender,confirmation_uri=confirmation_uri, subject=subject, override_access_lifespan=None)
        
            ret = {"message": "successfully sent registration email to user {}".format(
                new_user.username
            ), 
                "email": email,
                "confirmation_sender":confirmation_sender,
                "confirmation_uri":confirmation_uri,
                "subject": subject, 
            }
            app.logger.info(ret)
            return (jsonify(ret), 201)
        else:
            ret = {"message": "email {} already exists on DB!".format(email)}
            app.logger.info(ret)
            return (jsonify(ret), 303)
    else:
        ret = {"message":"user {} already exists on DB!".format(username)}
        app.logger.info(ret)
        return (jsonify(ret), 409)


@app.get("/api/finalize")
def finalize():

    registration_token = guard.read_token_from_header()
    user = guard.get_user_from_registration_token(registration_token)

    user.is_active = True  # user activation 
    db.session.commit()

    ret = {"access_token": guard.encode_jwt_token(user), "user": user.username}
    app.logger.info(ret)
    return (jsonify(ret), 200)


@app.route("/api/reset", methods=["POST"])
def reset():
    
    """Reset password email"""

    reset_sender=(APP_NAME, MAIL_USERNAME)
    reset_uri = RESET_URI
    subject_rest = SUBJECT_RESET

    req = request.get_json(force=True)
    email = req.get("email", None)

    if db.session.query(User).filter_by(email=email).count() > 0:
        if db.session.query(User).filter(User.email==email, User.is_active==True).scalar():
            # guard.send_reset_email(email, reset_sender=reset_sender, reset_uri=reset_uri, subject=subject_rest, override_access_lifespan=None)
            
            ret = {"message": "successfully sent password reset email to {}".format(email)}
            app.logger.info(ret)
            return (jsonify(ret), 200)
        else:
            ret = {"message": "{} account not activated! active it first!".format(email)}
            app.logger.info(ret)
            return (jsonify(ret), 403)
    else:
        ret = {"message": "email {} doest not exists on DB!".format(email)}
        app.logger.info(ret)
        return (jsonify(ret), 404)


@app.route("/api/reset_finalize", methods=["POST"])
def reset_finalize():

    """Reset password on database by token"""

    req = request.get_json(force=True)
    password = req.get("password", None)
    
    reset_token = guard.read_token_from_header()

    try:
        user = guard.validate_reset_token(reset_token)
        user.password = guard.hash_password(password)
        db.session.commit()
        ret = {"access_token": guard.encode_jwt_token(user), "user": user.username}
        return (jsonify(ret), 200)
    except Exception:
        ret = {"Error resetting user password by token:"}
        return ret, 500



if __name__ == "__main__":
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)        
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    db.create_all()
    app.debug = True
    app.run(threaded=True)
