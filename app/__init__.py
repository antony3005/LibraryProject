from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bibliotech'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliotech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

migrate = Migrate(app, db)

from app import routes