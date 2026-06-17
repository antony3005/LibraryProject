from flask            import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate    import Migrate
from typing           import Final
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

DB_CONECTION: Final[str] = 'mysql+mysqldb'
DB_USER:      Final[str] = 'gabriel'
DB_PASSWORD:  Final[str] = '709010'
DB_HOST:      Final[str] = 'localhost'
DB_PORT:      Final[str] = '3306'
DB_NAME:      Final[str] = 'bd_sistema_tecnico'

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']        = f"{DB_CONECTION}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Desabilita o rastreamento automático de modificações de objetos SQLAlchemy
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"]                     = 'sdaddasda4sdasd4s5d-4a6sdas84!!d8as49ds48'

db      = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
# Redireciona para a home caso tente acessar rota protegida deslogado
login_manager.login_view             = 'index'
login_manager.login_message          = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "warning"

bcrypt = Bcrypt(app)

from app.routes import index
from app.routes import cadastrar_produto
from app.routes import listar_produtos
from app.routes import visualizar_produto
from app.models import Categoria, Produto

# Usamos o contexto da aplicação para garantir que o Flask saiba 
# qual banco de dados manipular antes de subir o servidor
with app.app_context():
    if not Categoria.query.first():
        cat1 = Categoria(name = "Eletrônicos")
        cat2 = Categoria(name = "Alimentos")
        cat3 = Categoria(name = "Vestuário")
        
        db.session.add_all([cat1, cat2, cat3])
        db.session.commit()
        print("Categorias iniciais cadastradas com sucesso!")