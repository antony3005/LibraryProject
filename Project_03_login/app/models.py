from app      import db, login_manager
from datetime import datetime
from flask_login import UserMixin

# Função usada para retornar o user que será logado.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    id         = db.Column(db.Integer,     primary_key = True)
    name       = db.Column(db.String(20),  nullable = False)
    last_name  = db.Column(db.String(40),  nullable = False)
    email      = db.Column(db.String(50),  nullable = False)
    password   = db.Column(db.String(128), nullable = False)
    role       = db.Column(db.String(20),  nullable = False, default='comum')

class Categoria(db.Model):
    id   = db.Column(db.Integer,    primary_key = True,  autoincrement = True)
    name = db.Column(db.String(50), nullable    = True, unique         = True)
    # Relacionamento que permite acessar produtos de uma categoria: categoria.produtos
    products = db.relationship('Produto', backref = 'categoria', lazy = True)

class Produto(db.Model):
    id                 = db.Column(db.Integer,     primary_key = True)
    registerDate       = db.Column(db.DateTime,    nullable    = True, default = datetime.utcnow())
    name               = db.Column(db.String(100), nullable    = True)
    price              = db.Column(db.Float,       nullable    = True)
    quantity           = db.Column(db.Integer,     nullable    = True)
    manufacturing_date = db.Column(db.Date,        nullable    = True)
    expiration_date    = db.Column(db.Date,        nullable    = True)
    manufacturer       = db.Column(db.String(100), nullable    = True)
    # Chave Estrangeira
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable = True)