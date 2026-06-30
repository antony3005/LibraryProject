from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField, SelectField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange


class CadastroUsuario(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    sobrenome = StringField("Sobrenome", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    perfil = SelectField("Perfil", choices=[])
    submit = SubmitField("Cadastrar")


class CadastroLivro(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    titulo = StringField("Título", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    categoria = SelectField("Categoria", choices=[], coerce=int)
    editora = StringField("Editora", validators=[DataRequired()])
    ano = IntegerField(
        "Ano",
        validators=[
            DataRequired(),
            NumberRange(min=100, max=2100, message="Ano inválido")
        ]
    )
    quantidade = IntegerField(
        "Quantidade",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="Quantidade deve ser maior que 0")
        ]
    )
    submit = SubmitField("Cadastrar Livro")


class EditarLivro(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    titulo = StringField("Título", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    categoria = SelectField("Categoria", choices=[], coerce=int)
    editora = StringField("Editora", validators=[DataRequired()])
    ano = IntegerField(
        "Ano",
        validators=[
            DataRequired(),
            NumberRange(min=100, max=2100, message="Ano inválido")
        ]
    )
    quantidade = IntegerField(
        "Quantidade",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="Quantidade deve ser maior que 0")
        ]
    )
    submit = SubmitField("Salvar Alterações")


class EmprestarLivro(FlaskForm):
    usuario = StringField("Usuário", validators=[DataRequired()])
    livro = StringField("Livro", validators=[DataRequired()])
    submit = SubmitField("Emprestar")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Entrar")


class CategoriaForm(FlaskForm):
    nome = StringField("Nome da categoria", validators=[DataRequired()])
    submit = SubmitField("Salvar")


class SugestaoLivroForm(FlaskForm):
    titulo = StringField("Título do Livro", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    submit = SubmitField("Enviar Sugestão")
