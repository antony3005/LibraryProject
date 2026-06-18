from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # RF03: Criptografia
    role = db.Column(db.String(20), nullable=False, default='Aluno')  # RF01: Administrador, Professor, Aluno

    # Relacionamentos
    loans = db.relationship('Loan', backref='user', lazy=True)
    suggestions = db.relationship('BookSuggestion', backref='professor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # RF08: Validação de Limites de Empréstimos Ativos
    def can_borrow(self):
        active_loans = Loan.query.filter_by(user_id=self.id, returned=False).count()
        if self.role == 'Aluno' and active_loans >= 3:
            return False
        if self.role == 'Professor' and active_loans >= 5:
            return False
        return True


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)  #
    author = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)

    loans = db.relationship('Loan', backref='book', lazy=True)


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # RF06
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)  # RF06
    loan_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    return_due_date = db.Column(db.DateTime, nullable=False)
    returned = db.Column(db.Boolean, default=False)

    def calculate_due_date(self, user_role):
        days = 15 if user_role == 'Professor' else 7
        self.return_due_date = datetime.utcnow() + timedelta(days=days)

    @property
    def is_overdue(self):
        return not self.returned and datetime.utcnow() > self.return_due_date


class BookSuggestion(db.Model):
    __tablename__ = 'book_suggestions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)