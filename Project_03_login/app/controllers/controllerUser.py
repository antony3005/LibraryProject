from app.models  import User
from app         import db, login_manager
from flask_login import current_user

class ControllerUser():
    # Função usada para retornar o user que será logado.
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @staticmethod
    def isLoged() -> bool:
        return current_user.is_authenticated
    
    @staticmethod
    def getRole_CurrentUser() -> str:
        return current_user.role

    @staticmethod
    def checkAdminPermission() -> bool:
        return current_user.role == 'admin'