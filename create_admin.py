
from app import app, db
from app.models import Usuario, PerfilEnum

with app.app_context():
    db.create_all()

    if not Usuario.query.filter_by(email='admin@bibliotech.com').first():
        admin = Usuario(
            nome='Admin',
            sobrenome='BiblioTech',
            email='admin@bibliotech.com',
            perfil=PerfilEnum.ADMIN
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print(" Banco criado e admin cadastrado!")
        print("   Email: admin@bibliotech.com")
        print("   Senha: admin123")
    else:
        print("ℹ!Admin já existe. Banco atualizado.")
