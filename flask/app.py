from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_user:postgres_password@postgres/postgres_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, name):
        self.name = name


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')

    if name:
        user = User(name)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'})
    else:
        return jsonify({'error': 'Invalid request'})


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = [{'id': user.id, 'name': user.name} for user in users]
    return jsonify({'users': result})


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5000)
