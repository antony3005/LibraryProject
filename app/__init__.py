from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bibliotech'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliotech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "login"

migrate = Migrate(app, db)


from app import models
from app import auth
from app import routes