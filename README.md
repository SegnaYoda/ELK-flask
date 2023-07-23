## ports:

* 8000: Server
* 5000: Logstash TCP input
* 5044: Logstash Beats input
* 9600: Logstash monitoring API
* 9200: Elasticsearch HTTP
* 9300: Elasticsearch TCP transport
* 5601: Kibana

## Commands

`docker-compose build`

`docker-compose up -d`

`docker-compose down -v`

# JWT Login Flask

This is a Flask API JWT based login authentication. 

You can check my [blog post](https://patriciadourado.com/frompat/jwt-login-flask/) of this project if you need more details about Python Virtual Environment setup or other stuffs. I will try to update it as often as possible.

## SQLAlchemy

SQLAlchemy was used as the Python ORM for accessing data from the database and facilitate the communication between app and db converting function calls to SQL statements;

Do not forget to change ***'SQLALCHEMY_DATABASE_URI'*** to your own here:

**api.py**
```
app.config['SQLALCHEMY_DATABASE_URI'] = postgresql://user_database:password@hostname:5432/database_name'
```

## PostgreSQL

The database used was PostgreSQL (before being deployed it was modeled through *pgAdmin 4* interface) and the SQL for the created users table is the following:

```
CREATE TABLE public.users
(
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    username text COLLATE pg_catalog."default" NOT NULL,
    password text COLLATE pg_catalog."default" NOT NULL,
    roles text COLLATE pg_catalog."default",
    is_active boolean,
    CONSTRAINT users_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE public.users
    OWNER to (insert here your user_database)
```
Make sure to create the database before running the ```api.py``` 

## Endpoints

Some endpoints were defined to be consumed by the frontend application, they are:

**1. /api/**

The first endpoint is the confirmation our API is up running!

```python
@app.route('/api/')
def home():
    return {"JWT Server Application":"Running!"}, 200
```
**2. /api/login**

The second endpoint receives the user credentials (by POST request) and authenticates/logs it with flask-praetorian 'authenticate' method issuing a user JWT access token and returning a 200 code with the token;

**3. /api/refresh**

The third endpoint refreshes (by POST request) an existing JWT creating a new one with a new access expiration, returning a 200 code with the new token;

**4. /api/protected**

The fourth endpoint is a protected endpoint which requires a header with a valid JWT using the ```@flask_praetorian.auth_required``` decorator. The endpoint returns a message with the current user username as a secret message;

**5. /api/registration**

The fifth endpoint is a simple user registration without requiring user email (for now), with the password hash method being invoked only to demonstrate insertion into database if its a new user;

## Flask-praetorian

To let the things easier Flask-praetorian was used to handle the hard logic by itself. Among the advantages of using Flask-praetorian in this API (where the most important is undoubtedly allowing to use JWT token for authentication) are:

* Hash passwords for storing in database;
* Verify plaintext passwords against the hashed, stored versions;
* Generate authorization tokens upon verification of passwords;
* Check requests to secured endpoints for authorized tokens;
* Supply expiration of tokens and mechanisms for refreshing them;
* Ensure that the users associated with tokens have necessary roles for access;

You can check Flask-praetorian documentation here: [Flask-praetorian](https://flask-praetorian.readthedocs.io/en/latest/index.html#table-of-contents)
