from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    usuario = db.Column(db.String(50), unique=True)
    senha = db.Column(db.String(255))
    perfil = db.Column(db.String(20))

    def set_password(self, password):
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha, password)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True)
    titulo = db.Column(db.String(200))
    autor = db.Column(db.String(200))
    categoria = db.Column(db.String(100))
    editora = db.Column(db.String(100))
    ano = db.Column(db.Integer)
    quantidade = db.Column(db.Integer)
    disponiveis = db.Column(db.Integer)


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    livro_id = db.Column(db.Integer, db.ForeignKey('book.id'))

    data_emprestimo = db.Column(db.DateTime, default=datetime.utcnow)
    data_devolucao = db.Column(db.DateTime)

    devolvido = db.Column(db.Boolean, default=False)


class BookSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    autor = db.Column(db.String(100))
    professor = db.Column(db.String(100))

    