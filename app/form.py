from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField, SelectField, PasswordField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange


class CadastroUsuario(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    sobrenome = StringField("Sobrenome", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])

    senha = PasswordField("Senha", validators=[Optional(), Length(min=8)])

    perfil = SelectField("Perfil", choices=[])

    submit = SubmitField("Enviar")


class CadastroLivro(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    titulo = StringField("Titulo", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    categoria = StringField("Categoria", validators=[DataRequired()])
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

    submit = SubmitField("Enviar")


class EditarLivro(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    titulo = StringField("Titulo", validators=[DataRequired()])
    autor = StringField("Autor", validators=[DataRequired()])
    categoria = StringField("Categoria", validators=[DataRequired()])
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

    submit = SubmitField("Enviar")


class EmprestarLivro(FlaskForm):
    usuario = StringField("Usuario", validators=[DataRequired()])
    livro = StringField("Livro", validators=[DataRequired()])

    submit = SubmitField("Enviar")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField("Enviar")

