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

CATEGORIAS_PADRAO = [
    "Ficção", "Não Ficção", "Fantasia", "Ficção Científica", "Distopia",
    "Suspense", "Thriller", "Terror", "Ação", "Aventura", "Romance",
    "Drama", "Poesia", "Conto", "Crônica", "Policial", "Histórico",
    "Biografia", "Autoajuda", "Infantil", "Juvenil",
]

with app.app_context():
    db.create_all()
    nomes_existentes = {c.nome.lower() for c in models.Categoria.query.all()}
    for nome in CATEGORIAS_PADRAO:
        if nome.lower() not in nomes_existentes:
            db.session.add(models.Categoria(nome=nome))
    db.session.commit()