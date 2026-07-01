import enum
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class PerfilEnum(enum.Enum):
    ALUNO = "aluno"
    PROFESSOR = "professor"
    ADMIN = "admin"


class Usuario(db.Model, UserMixin):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    sobrenome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(255))

    perfil = db.Column(db.Enum(PerfilEnum, native_enum=False), nullable=False)

    emprestimos = db.relationship(
        'Emprestimo',
        backref='usuario',
        lazy=True
    )

    def set_password(self, password):
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha, password)

    def __repr__(self):
        return f"<Usuario {self.id} - {self.nome} {self.sobrenome} - {self.email}>"


class Livro(db.Model):
    __tablename__ = "livro"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True)
    titulo = db.Column(db.String(200))
    autor = db.Column(db.String(200))
    editora = db.Column(db.String(100))
    ano = db.Column(db.Integer)
    quantidade = db.Column(db.Integer)
    disponiveis = db.Column(db.Integer)
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categoria.id")
    )

    emprestimos = db.relationship(
        'Emprestimo',
        backref='livro',
        lazy=True
    )

    def __repr__(self):
        return f"<Livro {self.id} - {self.titulo} ({self.autor})>"


class Emprestimo(db.Model):
    __tablename__ = "emprestimo"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.id'))

    data_emprestimo = db.Column(db.DateTime, default=datetime.utcnow)
    data_devolucao = db.Column(db.DateTime)
    devolucao = db.Column(db.Boolean, default=False)

    def definir_prazo(self, perfil: PerfilEnum):
        if self.data_emprestimo is None:
            self.data_emprestimo = datetime.utcnow()

        if perfil == PerfilEnum.ALUNO:
            dias = 7
        elif perfil == PerfilEnum.PROFESSOR:
            dias = 15
        else:
            dias = 30

        self.data_devolucao = self.data_emprestimo + timedelta(days=dias)


class BookSuggestion(db.Model):
    __tablename__ = "book_suggestion"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    autor = db.Column(db.String(100))
    professor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    professor = db.relationship('Usuario', backref='sugestoes')


class Categoria(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

    livros = db.relationship(
        "Livro",
        backref="categoria",
        lazy=True
    )

    def __repr__(self):
        return f"{self.nome}"
