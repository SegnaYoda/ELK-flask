import time
from flask import Flask, render_template, flash, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy


POSTGRES_USER = 'postgres_user'
POSTGRES_PASSWORD = 'postgres_password'
POSTGRES_DB = 'postgres_db'


app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2://{user}:{passwd}@postgres:{port}'.format(
        user=POSTGRES_USER,
        passwd=POSTGRES_PASSWORD,
        port=5432,
        )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = POSTGRES_PASSWORD


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(200))

    def __init__(self, name, email):
        self.name = name
        self.email = email


def database_initialization_sequence():
    db.create_all()
    test_rec = User(
            'John Doe',
            'Foobar Ave@mail.com')

    db.session.add(test_rec)
    db.session.rollback()
    db.session.commit()


@app.route('/users', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if not request.form['name'] or not request.form['city'] or not request.form['addr']:
            flash('Please enter all the fields', 'error')
        else:
            user = User(
                    request.form['name'],
                    request.form['email'])

            db.session.add(user)
            db.session.commit()
            flash('User was succesfully added')
            return redirect(url_for('home'))
    return render_template('show_all.html', user=User.query.all())


if __name__ == '__main__':
    dbstatus = False
    while dbstatus == False:
        try:
            db.create_all()
        except:
            time.sleep(2)
        else:
            dbstatus = True
    database_initialization_sequence()
    app.run(debug=True, host='0.0.0.0')
