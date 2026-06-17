from flask_wtf          import FlaskForm
from wtforms            import StringField, FloatField, IntegerField, DateField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Email, Optional, EqualTo, ValidationError
from app.models         import Produto, User
from app.controllers.controllerProduto import ControllerProduto

from app import db, bcrypt


class LoginForm(FlaskForm):
    email            = StringField('E-mail',                  validators = [DataRequired(), Email()])
    password         = PasswordField('Senha:',                validators = [DataRequired()])
    btn_submit       = SubmitField("Entrar")

    def login(self):
        # Busca o usuário no banco de dados
        user = User.query.filter_by(email = self.email.data).first()
        # Validação de senha
        if user and bcrypt.check_password_hash(user.password, self.password.data.encode('utf-8')):
            return user
        return None

class UserForm(FlaskForm):
    name             = StringField('Primeiro nome:',          validators = [DataRequired()])
    last_name        = StringField('Sobrenome:',              validators = [DataRequired()])
    email            = StringField('E-mail',                  validators = [DataRequired(), Email()])
    password         = PasswordField('Senha:',                validators = [DataRequired()])
    pwd_confirmation = PasswordField('Confirmação de Senha:', validators = [DataRequired(), EqualTo('password')])
    role             = SelectField('Nível de Acesso', choices = [('comum', 'Usuário Comum'), ('admin', 'Administrador')], validators = [DataRequired()])
    btn_submit       = SubmitField("Cadastrar")

    def validate_email(self, email):
        if User.query.filter_by(email = self.email.data).first():
            raise ValidationError('Já existe um usuário cadastrado com esse email!!')
    
    def saveUser(self):
        pwd  = bcrypt.generate_password_hash(self.password.data.encode('utf-8'))
        user = User(name       = self.name.data,
                    last_name  = self.last_name.data,
                    email      = self.email.data,
                    password   = pwd)
        db.session.add(user)
        db.session.commit()
        return user

class ProdutoForm(FlaskForm):
    name               = StringField('Nome do Produto',           validators=[DataRequired()])
    price              = FloatField('Preço',                      validators=[DataRequired(), NumberRange(min = 0.01)])
    quantity           = IntegerField('Quantidade Disponível',    validators=[DataRequired(), NumberRange(min = 0)])
    manufacturing_date = DateField('Data de Fabricação',          validators=[DataRequired()], format='%Y-%m-%d')
    expiration_date    = DateField('Data de Validade (Opcional)', format='%Y-%m-%d', validators=[Optional()])
    manufacturer       = StringField('Fabricante',                validators=[DataRequired()])
    # Parâmetro "Coercion" para int garante que o ID da categoria retorne como número
    categoria_id       = SelectField('Categoria', coerce = int, validators=[DataRequired()])
    submit             = SubmitField('Salvar Produto')

    def saveData(self):
        new_product = Produto(
            name               = self.name.data,
            price              = self.price.data,
            quantity           = self.quantity.data,
            manufacturing_date = self.manufacturing_date.data,
            expiration_date    = self.expiration_date.data,
            manufacturer       = self.manufacturer.data,
            categoria_id       = self.categoria_id.data)
        # Salva novo produto no banco de dados
        ControllerProduto.registerNewProduct(new_product)        