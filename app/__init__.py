from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bibliotech'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliotech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from app import routes

with app.app_context():
    db.create_all()