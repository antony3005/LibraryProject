from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional


class CadastroUsuario(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
    sobrenome = StringField("Sobrenome", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])

    senha = PasswordField("Senha", validators=[Optional(), Length(min=8)])

    perfil = SelectField("Perfil", choices=[])

    submit = SubmitField("Enviar")
