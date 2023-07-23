import os
import time

import elasticapm

from flask import Flask, render_template, flash, redirect, request, url_for, jsonify, make_response
from dotenv import load_dotenv

from flask.wrappers import Request
from flask_migrate import Migrate
import flask_praetorian
import flask_cors
from flask_mail import Mail

from models import User, db
from apm_middleware import init_app as init_apm_middleware

load_dotenv()


APP_NAME = os.getenv('APP_NAME')
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
SECRET_KEY = os.getenv('SECRET_KEY')
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT  = os.getenv('MAIL_PORT')
MAIL_USERNAME  = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD  = os.getenv('MAIL_PASSWORD')
SUBJECT = os.getenv('SUBJECT')
SUBJECT_RESET = os.getenv('SUBJECT_RESET')
CONFIRMATION_URI = os.getenv('CONFIRMATION_URI')
RESET_URI = os.getenv('RESET_URI')


# Initialize flask app for the example
app = Flask(__name__)

app.debug = True
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}

guard = flask_praetorian.Praetorian()
cors = flask_cors.CORS()
# Initialize the flask-praetorian instance for the app
guard.init_app(app, User)

# Initialize the database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)

db.init_app(app)

# Initializes CORS so that the api_tool can talk to the example app
cors.init_app(app)


# configuration of mail
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = (APP_NAME, MAIL_USERNAME)
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#Initialize Mail extension
mail = Mail()
mail.init_app(app)

app = Flask(__name__)

app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'apm_system',
    'SECRET_TOKEN': 'nIncXi7cSf8e43lvV4SE',
    'SERVER_URL': 'http://0.0.0.0:8200',
}
elasticapm.init_app(app)
init_apm_middleware(app)

# Set up some routes for the example
@app.route('/api/')
def home():
    return {"JWT Server Application":"Running!"}, 200

  
@app.route('/api/login', methods=['POST'])
def login():
    """
    Logs a user in by parsing a POST request containing user credentials and
    issuing a JWT token.
    .. example::
       $ curl http://localhost:5000/api/login -X POST \
         -d '{"username":"myusername","password":"mypassword"}'
    """
    req = request.get_json(force=True)

    username = req.get('username', None)
    password = req.get('password', None)
    user = db.session.query(User).filter_by(username=username).first()

    if user:
        if guard._verify_password(password, user.password):
            ret = {'access_token': guard.encode_jwt_token(user)}
            return (jsonify(ret), 200)
        else:
            ret = {'access_token': ''}
            return (jsonify(ret), 401)
    else:
        ret = {'access_token': ''}
        return (jsonify(ret), 401)

  
@app.route('/api/refresh', methods=['POST'])
def refresh():
    """
    Refreshes an existing JWT by creating a new one that is a copy of the old
    except that it has a refreshed access expiration.
    .. example::
       $ curl http://localhost:5000/api/refresh -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    print("refresh request")
    old_token = Request.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    ret = {'access_token': new_token}
    return ret, 200
  
  
@app.route('/api/protected')
@flask_praetorian.auth_required
def protected():
    """
    A protected endpoint. The auth_required decorator will require a header
    containing a valid JWT
    .. example::
       $ curl http://localhost:5000/api/protected -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    return {'message': 'protected endpoint (allowed usr {})'.format(flask_praetorian.current_user().username)}


@app.route('/api/registration', methods=['POST'])
def registration():
    
    """Register user with validation email"""

    subject = SUBJECT
    confirmation_sender=(APP_NAME, MAIL_USERNAME)
    confirmation_uri = CONFIRMATION_URI
    
    req = request.get_json(force=True)
    username = req.get('username', None)
    password = req.get('password', None)
    email = req.get('email', None)
    
    if db.session.query(User).filter_by(username=username).count() < 1:
        if db.session.query(User).filter_by(email=email).count() < 1:
            new_user = User(
                username=username,
                email=email,
                password=guard.hash_password(password),
                roles='user',
            )
            db.session.add(new_user)
            db.session.commit()
        
            guard.send_registration_email(email, user=new_user, confirmation_sender=confirmation_sender,confirmation_uri=confirmation_uri, subject=subject, override_access_lifespan=None)
        
            ret = {'message': 'successfully sent registration email to user {}'.format(
                new_user.username
            )}
            return (jsonify(ret), 201)
        else:
            ret = {'message': 'email {} already exists on DB!'.format(email)}
            return (jsonify(ret), 303)
    else:
        ret = {'message':'user {} already exists on DB!'.format(username)}
        return (jsonify(ret), 409)
    
    
@app.route('/api/finalize', methods=['GET'])
def finalize():
    
    registration_token = guard.read_token_from_header()
    user = guard.get_user_from_registration_token(registration_token)
    
    # user activation 
    user.is_active = True
    db.session.commit()
    
    ret = {'access_token': guard.encode_jwt_token(user), 'user': user.username}
    print(ret)
    return (jsonify(ret), 200)


@app.route('/api/reset', methods=['POST'])
def reset():
    
    """Reset password email"""

    reset_sender=(APP_NAME, MAIL_USERNAME)
    reset_uri = RESET_URI
    subject_rest = SUBJECT_RESET

    req = request.get_json(force=True)
    email = req.get('email', None)

    if db.session.query(User).filter_by(email=email).count() > 0:
        if db.session.query(User).filter(User.email==email, User.is_active==True).scalar():
            guard.send_reset_email(email, reset_sender=reset_sender, reset_uri=reset_uri, subject=subject_rest, override_access_lifespan=None)
            
            ret = {'message': 'successfully sent password reset email to {}'.format(email)}
            return (jsonify(ret), 200)
        else:
            ret = {'message': '{} account not activated! active it first!'.format(email)}
            return (jsonify(ret), 403)
    else:
        ret = {'message': 'email {} doest not exists on DB!'.format(email)}
        return (jsonify(ret), 404)


@app.route('/api/reset_finalize', methods=['POST'])
def reset_finalize():

    """Reset password on database by token"""

    req = request.get_json(force=True)
    password = req.get('password', None)
    
    reset_token = guard.read_token_from_header()

    try:
        user = guard.validate_reset_token(reset_token)
        user.password = guard.hash_password(password)
        db.session.commit()
        ret = {'access_token': guard.encode_jwt_token(user), 'user': user.username}
        return (jsonify(ret), 200)
    except Exception:
        ret = {"Error resetting user password by token:"}
        return ret, 500



if __name__ == '__main__':
    dbstatus = False
    while dbstatus == False:
        try:
            db.create_all()
        except:
            time.sleep(2)
        else:
            dbstatus = True
    app.run(debug=True, host='0.0.0.0')
